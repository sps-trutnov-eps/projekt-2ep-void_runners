from dataclasses import dataclass
from engine.cue import cue_sequence as seq
from engine.cue.entities import cue_entity_types as en
from engine.cue.cue_state import GameState
from sps_state import SpsState

from engine.cue.components.cue_transform import Transform
from engine.cue.components.cue_model import ModelRenderer
from engine.cue.phys.cue_phys_types import PhysRay

from pygame.math import Vector3 as Vec3, Vector2 as Vec2
from engine.cue.entities.cue_entity_utils import handle_transform_edit_mode

from engine.cue.entities.bt_static_mesh import BtStaticMesh
from engine.cue.rendering import cue_gizmos as gizmo

# a projectile entity that will travel in a direction until a collider or a hitbox is hit 

@dataclass(init=False, slots=True)
class SpsProjectile:
    def __init__(self, en_data: dict) -> None:
        self.pr_trans = Transform(en_data["t_pos"], en_data["t_rot"], en_data["t_scale"])
        self.model_overlay_rot = en_data["t_rot"]
        self.mesh_renderer = ModelRenderer(en_data, self.pr_trans)

        self.pr_hitbox_size = en_data["t_scale"].elementwise() * en_data["hitbox_scale"]
        self.pr_damage = en_data["projectile_damage"]

        self.pr_dir = en_data["projectile_dir"]
        self.pr_vel = en_data["projectile_velocity"]

        self.local_name = en_data["bt_en_name"]

        seq.next(self.tick)

    def tick(self) -> None:
        if self.local_name is None:
            return # entity despawned, stop tick loop

        # TODO: apply tick vel and pos changes
        frame_dist = self.pr_vel * GameState.delta_time
        new_pos = self.pr_trans._pos + self.pr_dir * frame_dist

        # TODO: check for hitbox hits
        pr_ray = PhysRay.make(self.pr_trans._pos, self.pr_dir, self.pr_hitbox_size)
        
        coll_hit = GameState.collider_scene.first_hit(pr_ray, frame_dist)
        hb_hit = SpsState.hitbox_scene.first_hit(pr_ray, frame_dist if coll_hit is None else coll_hit.tmin)

        if hb_hit is not None:
            hb_hit.usr.on_damage(self.pr_damage, Vec3(*hb_hit.pos))
            GameState.entity_storage.despawn(self.local_name)
            self.local_name = None

        elif coll_hit is not None:
            GameState.entity_storage.despawn(self.local_name)
            self.local_name = None

        dir_rot = Vec3() # TODO: calc rot from projectile dir

        self.pr_trans.set_pos_rot(new_pos, self.model_overlay_rot + dir_rot)
        seq.next(self.tick)

    # == entity hooks ==

    @staticmethod
    def spawn(en_data: dict) -> 'SpsProjectile':
        return SpsProjectile(en_data)

    def despawn(self) -> None:
        self.mesh_renderer.hide() # hide until this class gets garbage collected

    @staticmethod
    def dev_tick(s: dict | None, dev_state: en.DevTickState, en_data: dict) -> dict:
        if s is None:
            if en_data["t_pos"] is None:
                en_data["t_pos"] = dev_state.suggested_initial_pos

            dev_data = dict(en_data)
            dev_data["t_rot"] = Vec3()

            # in editor BtStaticMesh is used for preview
            s = {"mesh": BtStaticMesh(dev_data), "en_data": dict(en_data)}
        elif en_data != s["en_data"]:
            del s["mesh"]
            dev_data = dict(en_data)
            dev_data["t_rot"] = Vec3()

            s["mesh"] = BtStaticMesh(dev_data)
            s["en_data"] = dict(en_data)

        # handle trasnsform editing
        if dev_state.is_entity_selected:
            handle_transform_edit_mode(s, dev_state, en_data)

        # draw hitbox

        if dev_state.is_entity_selected:
            hitbox = en_data["t_scale"].elementwise() * en_data["hitbox_scale"]
            min_p = en_data["t_pos"] - (hitbox / 2)
            max_p = en_data["t_pos"] + (hitbox / 2)

            gizmo.draw_box(min_p, max_p, Vec3(1., .35, .35))

        return s

    pr_trans: Transform
    model_overlay_rot: Vec3

    pr_dir: Vec3
    pr_vel: float

    pr_hitbox_size: Vec3
    pr_damage: int

    view_space_trans: Transform
    mesh_renderer: ModelRenderer

    local_name: str | None

def gen_def_data():
    return {
        "t_pos": None,
        "t_rot": Vec3(),
        "t_scale": Vec3(1.0, 1.0, 1.0),
        "projectile_type": "bullet",
        "projectile_damage": 5,
        "projectile_dir": Vec3(0.0, 0.0, -1.0),
        "projectile_velocity": 4.,
        "hitbox_scale": Vec3(1.0, 1.0, 1.0),
        "a_model_mesh": "models/icosph.npz",
        "a_model_vshader": "shaders/base_cam.vert",
        "a_model_fshader": "shaders/unlit.frag",
        "a_model_albedo": "textures/def_white.png",
        "a_model_transparent": False,
        "a_model_uniforms": {},
    }

en.create_entity_type("sps_projectile", SpsProjectile.spawn, SpsProjectile.despawn, SpsProjectile.dev_tick, gen_def_data)