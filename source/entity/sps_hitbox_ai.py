import time

from dataclasses import dataclass
from engine.cue.entities import cue_entity_types as en
from engine.cue import cue_sequence as seq
from engine.cue.cue_state import GameState
from sps_state import SpsState

from engine.cue.entities.cue_entity_utils import handle_transform_edit_mode
from engine.cue.rendering import cue_gizmos as gizmo

from engine.cue.entities.bt_static_mesh import BtStaticMesh
from engine.cue.components.cue_transform import Transform
from engine.cue.components.cue_model import ModelRenderer
from engine.cue.phys.cue_phys_types import PhysAABB, PhysRay

from pygame.math import Vector3 as Vec3

# a semi-generic entity for most ai controlled enemies or npcs

@dataclass(init=False, slots=True)
class SpsHitboxAi:
    AI_TYPE_TABLE = {
        "enemy_turret": 0,
        "enemy_arial": 1,
    }
    AI_ARGO_DECAY = 15.

    TURRET_AIM_LERP_FACTOR = .15 * 60
    TURRET_AIM_ALIGN_TOLERANCE = .98

    def __init__(self, en_data: dict) -> None:
        self.ai_type = self.AI_TYPE_TABLE[en_data["ai_type"]]

        self.ai_trans = Transform(en_data["t_pos"], en_data["t_rot"], en_data["t_scale"])
        self.ai_model = ModelRenderer(en_data, self.ai_trans)

        self.ai_hitbox_scale = en_data["hitbox_scale"]
        self.ai_hitbox = PhysAABB.make(self.ai_trans._pos, self.ai_trans._scale.elementwise() * self.ai_hitbox_scale)

        self.ai_agro_level = 0.
        self.ai_target_last_seen_pos = Vec3()
        self.ai_target_last_seen_time = 0.

        if self.ai_type == 0:
            self.tr_view_dir = Vec3()
            self.tr_state = 0
        
        seq.next(self.tick)

    def tick(self) -> None:
        if self.ai_type == 0:
            self.tick_enemy_turret()

        elif self.ai_type == 1:
            self.tick_enemy_arial()

        seq.next(self.tick)

    # == ai impls ==

    def tick_enemy_turret(self) -> None:
        # check for player visibility

        target_dir = (SpsState.p_active_controller.p_pos - self.ai_trans._pos)
        target_dist = target_dir.length()
        
        if target_dist == 0.:
            return # both target and origin are at the same place, possible crash, just give up

        target_dir.normalize_ip()

        vis_ray = PhysRay.make(self.ai_trans._pos, target_dir)
        vis_hit = GameState.collider_scene.first_hit(vis_ray, target_dist)

        if vis_hit is None:
            self.ai_agro_level = 100.
            self.ai_target_last_seen_pos = Vec3(SpsState.p_active_controller.p_pos)
            self.ai_target_last_seen_time = time.perf_counter()

        else:
            self.ai_agro_level = max(0., self.ai_agro_level - self.AI_ARGO_DECAY * GameState.delta_time)

        if SpsState.ai_debug:
            gizmo.draw_text(self.ai_trans._pos, f"ai_type: {self.ai_type}\nai_argo_level: {self.ai_agro_level}\nai_vis: {vis_hit is None}", start_fade=float('inf'))

            # line_col = Vec3(1., .1, .1) if vis_hit is not None else Vec3(.1, 1., .1)
            # gizmo.draw_line(SpsState.p_active_controller.p_pos, self.ai_trans._pos, line_col, line_col)

            if self.ai_agro_level > 0.:
                gizmo.draw_box(self.ai_target_last_seen_pos - Vec3(.2, .2, .2), self.ai_target_last_seen_pos + Vec3(.2, .2, .2), Vec3(.35, 1., 1.))

        # aim for player

        if vis_hit is None:
            # player visible, align with player

            t = min(1., self.TURRET_AIM_LERP_FACTOR * GameState.delta_time)
            self.tr_view_dir = self.tr_view_dir * (1. - t) + target_dir * t
            self.tr_view_dir.normalize_ip()

            if self.tr_view_dir.dot(target_dir) >= self.TURRET_AIM_ALIGN_TOLERANCE:
                self.tr_state = 3
            else:
                self.tr_state = 2

            if SpsState.ai_debug:
                line_col = Vec3(.35, 1., .35) if self.tr_state == 3 else Vec3(.35, .35, 1.)
                gizmo.draw_line(self.ai_trans._pos, self.ai_trans._pos + self.tr_view_dir * 5., line_col, line_col)

        elif self.ai_agro_level > 0.:
            self.tr_state = 1

        else:
            self.tr_state = 0

    def tick_enemy_arial(self) -> None:
        pass

    # == entity hooks ==

    @staticmethod
    def spawn(en_data: dict) -> 'SpsHitboxAi':
        return SpsHitboxAi(en_data)

    def despawn(self) -> None:
        self.ai_model.hide()
        SpsState.hitbox_scene.remove_coll(self.ai_hitbox)

    @staticmethod
    def dev_tick(s: dict | None, dev_state: en.DevTickState, en_data: dict) -> dict:
        if s is None:
            if en_data["t_pos"] is None:
                en_data["t_pos"] = dev_state.suggested_initial_pos

            s = {"mesh": BtStaticMesh(en_data), "en_data": dict(en_data)}
        elif en_data != s["en_data"]:
            # update mesh
            del s["mesh"]
            s["mesh"] = BtStaticMesh(en_data)
            s["en_data"] = dict(en_data)

        if dev_state.is_entity_selected:
            handle_transform_edit_mode(s, dev_state, en_data)

        # draw hitbox

        if dev_state.is_entity_selected:
            hitbox = en_data["t_scale"].elementwise() * en_data["hitbox_scale"]
            min_p = en_data["t_pos"] - (hitbox / 2)
            max_p = en_data["t_pos"] + (hitbox / 2)

            gizmo.draw_box(min_p, max_p, Vec3(1., .35, .35))

        return s

    # which ai is used for this entity
    # - 0 - enemy_turret
    # - 1 - enemy_arial
    ai_type: int

    ai_trans: Transform
    ai_model: ModelRenderer

    ai_hitbox_scale: Vec3
    ai_hitbox: PhysAABB

    ai_agro_level: float
    ai_target_last_seen_pos: Vec3
    ai_target_last_seen_time: float

    # turret vars

    tr_view_dir: Vec3
    tr_state: int

def gen_def_data() -> dict:
    return {
        "t_pos": None,
        "t_rot": Vec3(0.0, 0.0, 0.0),
        "t_scale": Vec3(1.0, 1.0, 1.0),
        "ai_type": "enemy_turret",
        "hitbox_scale": Vec3(1.0, 1.0, 1.0),
        "hitbox_hp": 120,
        "a_model_mesh": "models/icosph.npz",
        "a_model_vshader": "shaders/base_cam.vert",
        "a_model_fshader": "shaders/unlit.frag",
        "a_model_albedo": "textures/def_white.png",
        "a_model_transparent": False,
    }

en.create_entity_type("sps_hitbox_ai", SpsHitboxAi.spawn, SpsHitboxAi.despawn, SpsHitboxAi.dev_tick, gen_def_data)