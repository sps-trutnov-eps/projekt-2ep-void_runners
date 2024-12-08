from dataclasses import dataclass
from engine.cue import cue_sequence as seq
from engine.cue.entities import cue_entity_types as en
from engine.cue.cue_state import GameState

from engine.cue.components.cue_transform import Transform
from engine.cue.components.cue_model import ModelRenderer

from pygame.math import Vector3 as Vec3, Vector2 as Vec2
from engine.cue.entities.cue_entity_utils import handle_transform_edit_mode

from engine.cue.entities.bt_static_mesh import BtStaticMesh
from engine.cue.rendering import cue_gizmos as gizmo

import prefabs
from sps_state import SpsState

import numpy as np

@dataclass(init=False, slots=True)
class SpsSpawner:
    def __init__(self, en_data: dict) -> None:
        self.drone_spawn_cooldown = 0.
        self.next_drone_id = 0

        self.mesh_trans = Transform(en_data["t_pos"], en_data["t_rot"], Vec3(en_data["t_scale"]))
        self.mesh_renderer = ModelRenderer(en_data, self.mesh_trans)

        self.drone_spawn_pos = Vec3(*(self.mesh_trans._trans_matrix @ np.array([*en_data["spawn_pos"], 1.], dtype=np.float32))[0:3])
        self.local_name = en_data["bt_en_name"]

        seq.next(self.tick)

    def tick(self) -> None:
        if GameState.current_time - self.drone_spawn_cooldown > .5:
            self.drone_spawn_cooldown = GameState.current_time

            drone_prefab = prefabs.load_prefab(f"__{self.local_name}_drone_{self.next_drone_id}", "prefabs/drone.json")
            self.next_drone_id += 1

            drone_prefab[0][2]["t_pos"] = self.drone_spawn_pos

            prefabs.spawn_prefab(drone_prefab)

        seq.next(self.tick)

    # == entity hooks ==

    @staticmethod
    def spawn(en_data: dict) -> 'SpsSpawner':
        return SpsSpawner(en_data)

    def despawn(self) -> None:
        self.mesh_renderer.despawn()

    @staticmethod
    def dev_tick(s: dict | None, dev_state: en.DevTickState, en_data: dict) -> dict:
        if s is None:
            # in editor BtStaticMesh is used for preview

            if en_data["t_pos"] is None:
                en_data["t_pos"] = dev_state.suggested_initial_pos

            s = {"mesh": BtStaticMesh(en_data), "en_data": dict(en_data)}
        elif en_data != s["en_data"]:
            del s["mesh"]
            s["mesh"] = BtStaticMesh(en_data)
            s["en_data"] = dict(en_data)

        # handle trasnsform editing
        if dev_state.is_entity_selected:
            handle_transform_edit_mode(s, dev_state, en_data)

            fire_pos = Vec3(*(s["mesh"].mesh_trans._trans_matrix @ np.array([*en_data["spawn_pos"], 1.], dtype=np.float32))[0:3])
            line_col = Vec3(1., 1., .35)

            gizmo.draw_line(fire_pos + Vec3(.1, .0, .0), fire_pos - Vec3(.1, .0, .0), line_col, line_col)
            gizmo.draw_line(fire_pos + Vec3(.0, .1, .0), fire_pos - Vec3(.0, .1, .0), line_col, line_col)
            gizmo.draw_line(fire_pos + Vec3(.0, .0, .1), fire_pos - Vec3(.0, .0, .1), line_col, line_col)

        return s

    drone_spawn_cooldown: float
    drone_spawn_pos: Vec3
    next_drone_id: int

    mesh_trans: Transform
    mesh_renderer: ModelRenderer

    local_name: str

def gen_def_data():
    return {
        "t_pos": None,
        "t_rot": Vec3(0.0, 0.0, 0.0),
        "t_scale": Vec3(1.0, 1.0, 1.0),
        "spawn_pos": Vec3(0.0, 0.0, 0.0),
        "a_model_mesh": "models/icosph.npz",
        "a_model_vshader": "shaders/base_cam.vert",
        "a_model_fshader": "shaders/unlit.frag",
        "a_model_albedo": "textures/def_white.png",
        "a_model_transparent": False,
        "a_model_uniforms": {},
    }

en.create_entity_type("sps_spawner", SpsSpawner.spawn, SpsSpawner.despawn, SpsSpawner.dev_tick, gen_def_data)