from dataclasses import dataclass
from engine.cue import cue_sequence as seq
from engine.cue.entities import cue_entity_types as en
from engine.cue.cue_state import GameState

from engine.cue.components.cue_transform import Transform
from engine.cue.components.cue_model import ModelRenderer
from engine.cue.phys.cue_phys_types import PhysAABB, PhysRay

from pygame.math import Vector3 as Vec3, Vector2 as Vec2
from engine.cue.entities.cue_entity_utils import handle_transform_edit_mode

from engine.cue.entities.bt_static_mesh import BtStaticMesh
from engine.cue.rendering import cue_gizmos as gizmo

from sps_state import SpsState
from components.fire_emitter import FireEmitter
import prefabs

import numpy as np

@dataclass(init=False, slots=True)
class SpsSpawner:
    def __init__(self, en_data: dict) -> None:
        self.drone_spawn_cooldown = 0.
        self.next_drone_id = 0

        self.hitbox_health = en_data["hitbox_health"]
        self.hitbox = PhysAABB.make(en_data["t_pos"], en_data["t_scale"].elementwise() * en_data["hitbox_scale"], self)
        SpsState.hitbox_scene.add_coll(self.hitbox)

        self.fire_end_time = 0.
        self.fire_emitter = FireEmitter()
        self.fire_emitter.set_origin(en_data["t_pos"])

        self.mesh_trans = Transform(en_data["t_pos"], en_data["t_rot"], Vec3(en_data["t_scale"]))
        self.mesh_renderer = ModelRenderer(en_data, self.mesh_trans)

        self.drone_spawn_pos = Vec3(*(self.mesh_trans._trans_matrix @ np.array([*en_data["spawn_pos"], 1.], dtype=np.float32))[0:3])
        self.local_name = en_data["bt_en_name"]

        SpsState.active_enemy_count += 1

        seq.next(self.tick)

    def tick(self) -> None:
        if self.local_name is None:
            return # despawned

        if self.fire_end_time < GameState.current_time:
            self.fire_emitter.set_on_fire(False)

        if GameState.current_time - self.drone_spawn_cooldown > 1.5 and SpsState.active_drone_count < 15 and SpsState.p_health != 0:
            # test if player is visible to spawner

            player_diff = SpsState.p_active_controller.p_pos - self.drone_spawn_pos

            if player_diff.length_squared() != 0.:
                test_ray = PhysRay.make(self.drone_spawn_pos, player_diff.normalize())
                is_visible = GameState.collider_scene.first_hit(test_ray, player_diff.length()) is None
            else:
                is_visible = True

            if is_visible:
                # spawn drone

                self.drone_spawn_cooldown = GameState.current_time

                drone_prefab = prefabs.load_prefab(f"__{self.local_name}_drone_{self.next_drone_id}", "prefabs/drone.json")
                self.next_drone_id += 1

                drone_prefab[0][2]["t_pos"] = self.drone_spawn_pos
                prefabs.spawn_prefab(drone_prefab)

        seq.next(self.tick)

    def on_damage(self, damage: int, hit_pos: Vec3) -> None:
        if self.local_name is None:
            return

        self.hitbox_health -= damage

        if self.hitbox_health <= 0:
            self.fire_emitter.set_on_fire(False)

            debris_prefab = prefabs.load_prefab(self.local_name, "prefabs/spawner_debris.json")
            
            debris_prefab[0][2]["t_pos"] = self.mesh_trans._pos
            debris_prefab[0][2]["t_rot"] = self.mesh_trans._rot
            debris_prefab[1][2]["t_pos"] = self.mesh_trans._pos

            GameState.entity_storage.despawn(self.local_name)
            prefabs.spawn_prefab(debris_prefab)

    def on_force(self, active_force: Vec3) -> None:
        pass

    def set_fire(self, fire_lifetime: float) -> None:
        if self.local_name is None:
            return

        self.fire_end_time = GameState.current_time + fire_lifetime
        self.fire_emitter.set_on_fire(True)

    # == entity hooks ==

    @staticmethod
    def spawn(en_data: dict) -> 'SpsSpawner':
        return SpsSpawner(en_data)

    def despawn(self) -> None:
        self.local_name = None

        SpsState.active_enemy_count -= 1

        self.mesh_renderer.despawn()
        SpsState.hitbox_scene.remove_coll(self.hitbox)

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

            # draw hitbox / spawn pos gizmos

            hitbox = en_data["t_scale"].elementwise() * en_data["hitbox_scale"]
            min_p = en_data["t_pos"] - (hitbox / 2)
            max_p = en_data["t_pos"] + (hitbox / 2)

            gizmo.draw_box(min_p, max_p, Vec3(1., .35, .35))

            fire_pos = Vec3(*(s["mesh"].mesh_trans._trans_matrix @ np.array([*en_data["spawn_pos"], 1.], dtype=np.float32))[0:3])
            line_col = Vec3(1., 1., .35)

            gizmo.draw_line(fire_pos + Vec3(.1, .0, .0), fire_pos - Vec3(.1, .0, .0), line_col, line_col)
            gizmo.draw_line(fire_pos + Vec3(.0, .1, .0), fire_pos - Vec3(.0, .1, .0), line_col, line_col)
            gizmo.draw_line(fire_pos + Vec3(.0, .0, .1), fire_pos - Vec3(.0, .0, .1), line_col, line_col)

        return s

    drone_spawn_cooldown: float
    drone_spawn_pos: Vec3
    next_drone_id: int

    hitbox: PhysAABB
    hitbox_health: int
    fire_end_time: float
    fire_emitter: FireEmitter

    mesh_trans: Transform
    mesh_renderer: ModelRenderer

    local_name: str | None

def gen_def_data():
    return {
        "t_pos": None,
        "t_rot": Vec3(0.0, 0.0, 0.0),
        "t_scale": Vec3(1.0, 1.0, 1.0),
        "spawn_pos": Vec3(0.0, 0.0, 0.0),
        "hitbox_scale": Vec3(1.0, 1.0, 1.0),
        "hitbox_health": 80,
        "a_model_mesh": "models/icosph.npz",
        "a_model_vshader": "shaders/base_cam.vert",
        "a_model_fshader": "shaders/unlit.frag",
        "a_model_albedo": "textures/def_white.png",
        "a_model_transparent": False,
        "a_model_uniforms": {},
    }

en.create_entity_type("sps_spawner", SpsSpawner.spawn, SpsSpawner.despawn, SpsSpawner.dev_tick, gen_def_data)