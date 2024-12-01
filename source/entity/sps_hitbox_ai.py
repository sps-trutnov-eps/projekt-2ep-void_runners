import time, random

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
from engine.cue.phys.cue_phys_types import PhysAABB, PhysRay, EPSILON

from pygame.math import Vector3 as Vec3
import numpy as np

# a semi-generic entity for most ai controlled enemies or npcs

@dataclass(init=False, slots=True)
class SpsHitboxAi:
    AI_TYPE_TABLE = {
        "enemy_turret": 0,
        "enemy_drone": 1,
    }
    AI_ARGO_DECAY = 12.

    # turret

    TURRET_AIM_SPEED_FACTOR = 1.2
    TURRET_AIM_ALIGN_TOLERANCE = .998
    TURRET_AIM_FIRE_PAUSE = 1.8
    TURRET_FIRE_COOLDOWN = .0
    TURRET_BURST_COOLDOWN = .05
    TURRET_BURST_LENGHT = .05

    TURRET_SCAN_COOLDOWN = 2.2
    TURRET_SCAN_SPEED_FACTOR = .8

    # drone

    DRONE_NAVIG_SPEED = 8.
    DRONE_NAVIG_ACCEL = 12.
    DRONE_NAVIG_MAX_SPEED = 2.5

    DRONE_NAVIG_TARGET_MARGIN = .2
    DRONE_NAVIG_NEXT_TARGET_COOLDOWN = 0.
    DRONE_NAVIG_MAX_ATTEMPTS = 4 
    DRONE_NAVIG_MAX_STUCK_TIME = 1.5

    def __init__(self, en_data: dict) -> None:
        self.hitbox_health = en_data["hitbox_health"]
        self.ai_type = self.AI_TYPE_TABLE[en_data["ai_type"]]

        self.ai_trans = Transform(en_data["t_pos"], en_data["t_rot"], en_data["t_scale"])
        self.ai_model = ModelRenderer(en_data, self.ai_trans)

        self.ai_fire_offset = np.array([*en_data["ai_fire_offset"], 1.], dtype=np.float32)
        self.ai_hitbox_size = self.ai_trans._scale.elementwise() * en_data["hitbox_scale"]
        self.ai_hitbox = PhysAABB.make(self.ai_trans._pos, self.ai_hitbox_size, self)
        SpsState.hitbox_scene.add_coll(self.ai_hitbox)

        self.ai_agro_level = 0.
        self.ai_target_last_seen_pos = Vec3()
        self.ai_target_last_seen_time = 0.

        if self.ai_type == 0:
            self.tr_initial_view_dir = Vec3(0., 0., 1.)
            self.tr_view_dir = Vec3(self.tr_initial_view_dir)
            self.tr_state = 0

            self.tr_fire_colldown = 0
            self.tr_next_projectile_id = 0

            self.tr_prefire_pause = GameState.current_time
        
        elif self.ai_type == 1:
            self.dr_vel = Vec3()

            self.dr_nav_nodes_to_travel = []
            self.dr_nav_target_pos = en_data["t_pos"]
            self.dr_nav_margin_cooldown = GameState.current_time

            self.dr_last_non_stuck_time = GameState.current_time
            self.dr_stuck = False
        
        self.local_name = en_data["bt_en_name"]

        seq.next(self.tick)

    def tick(self) -> None:
        if self.local_name is None:
            return # despawned

        self.ai_fire_pos = Vec3(*(self.ai_trans._trans_matrix @ self.ai_fire_offset)[0:3])

        if self.ai_type == 0:
            self.tick_enemy_turret()

        elif self.ai_type == 1:
            self.tick_enemy_drone()

        seq.next(self.tick)

    def on_damage(self, damage: int, hit_pos: Vec3) -> None:
        self.hitbox_health -= damage

        if self.local_name is None:
            return # entity despawned already, this case should be reachable, but it happens anyway... 

        if self.hitbox_health <= 0:
            # TODO: spawn particle debris

            GameState.entity_storage.despawn(self.local_name)
            self.local_name = None

        try:
            hit_dir = (hit_pos - self.ai_trans._pos).normalize()
            # TODO: pong view_dir a lil up on damage

        except:
            pass # malformed hit pos (hit_pos == self.ai_trans._pos), just ignore

    # == ai impls ==

    def tick_enemy_turret(self) -> None:
        # check for player visibility
        
        if SpsState.p_health != 0:

            target_dir = (SpsState.p_active_controller.p_pos - self.ai_fire_pos + Vec3(0., SpsState.p_active_controller.PLAYER_SIZE.y / 2, 0.))
            target_dist = target_dir.length()

            if target_dist == 0.:
                return # both target and origin are at the same place, possible crash, just give up

            target_dir.normalize_ip()

            vis_ray = PhysRay.make(self.ai_fire_pos, target_dir)
            vis_hit = GameState.collider_scene.first_hit(vis_ray, target_dist)

            is_visible = vis_hit is None
        else:
            is_visible = False

        if is_visible:
            self.ai_agro_level = 100.
            self.ai_target_last_seen_pos = Vec3(SpsState.p_active_controller.p_pos)
            self.ai_target_last_seen_time = time.perf_counter()

        else:
            self.ai_agro_level = max(0., self.ai_agro_level - self.AI_ARGO_DECAY * GameState.delta_time)

        # laser ray cast

        laser_ray = PhysRay.make(self.ai_fire_pos, self.tr_view_dir)
        laser_hit = GameState.collider_scene.first_hit(laser_ray)
        laser_length = laser_hit.tmin if laser_hit is not None else 1000.

        # debug gizmos

        if SpsState.cheat_ai_debug:
            # gizmo.draw_text(self.ai_trans._pos, f"ai_type: {self.ai_type}\nai_argo_level: {round(self.ai_agro_level, 2)}\nai_vis: {is_visible}\ntr_state: {self.tr_state}", start_fade=float('inf'))

            line_col = Vec3(.35, 1., .35) if self.tr_state == 3 else Vec3(.35, .35, 1.)
            gizmo.draw_line(self.ai_fire_pos, self.ai_fire_pos + self.tr_view_dir * laser_length, line_col, line_col)

        # aim for player

        if is_visible:
            # player visible, align with player

            view_diff = target_dir - self.tr_view_dir
            if view_diff.length_squared() != 0.:
                self.tr_view_dir += view_diff.normalize() * min(view_diff.length(), self.TURRET_AIM_SPEED_FACTOR * GameState.delta_time)
            
            try: self.tr_view_dir.normalize_ip()
            except: pass # this case (view_dir == [0, 0, 0]) is *very* unlikely, but still possible

            if self.tr_view_dir.dot(target_dir) >= self.TURRET_AIM_ALIGN_TOLERANCE:
                self.tr_state = 3
            else:
                self.tr_state = 2

            self.tr_scan_cooldown = 0

        elif self.ai_agro_level > 0.:
            # animate the turret scan with random movements around the last seen point
            if GameState.current_time - self.tr_scan_cooldown > self.TURRET_SCAN_COOLDOWN:
                self.tr_scan_cooldown = GameState.current_time
                self.tr_scan_target_dir = ((self.ai_target_last_seen_pos - self.ai_trans._pos).normalize() + Vec3(random.uniform(-.35, .35), random.uniform(-.35, .35), random.uniform(-.35, .35))).normalize()

            # interpolate around that scan dir
            view_diff = self.tr_scan_target_dir - self.tr_view_dir
            if view_diff.length_squared() != 0.:
                self.tr_view_dir += view_diff.normalize() * min(view_diff.length(), self.TURRET_SCAN_SPEED_FACTOR * GameState.delta_time)

            self.tr_state = 1

        else:
            view_diff = self.tr_initial_view_dir - self.tr_view_dir
            if view_diff.length_squared() != 0.:
                self.tr_view_dir += view_diff.normalize() * min(view_diff.length(), self.TURRET_SCAN_SPEED_FACTOR * GameState.delta_time)

            self.tr_state = 0
            self.tr_prefire_pause = GameState.current_time

        if (
            self.tr_state == 3 and # player visible
            time.perf_counter() - self.tr_fire_colldown > self.TURRET_FIRE_COOLDOWN and # no inter-bullet cooldown
            GameState.current_time - self.tr_prefire_pause > self.TURRET_AIM_FIRE_PAUSE # no prefire cooldown    
            ):
            proj_data = {
                "t_pos": self.ai_fire_pos,
                "t_rot": Vec3(),
                "t_scale": Vec3(.4, .4, .4),
                "projectile_type": "bullet",
                "projectile_damage": 20,
                "projectile_dir": Vec3(self.tr_view_dir),
                "projectile_velocity": 45,
                "hitbox_scale": Vec3(1.0, 1.0, 1.0),
                "a_model_mesh": "models/chair.npz",
                "a_model_vshader": "shaders/base_cam.vert",
                "a_model_fshader": "shaders/unlit.frag",
                "a_model_albedo": "textures/proto/Dark/texture_07.png",
                "a_model_transparent": False,
            }

            GameState.entity_storage.spawn("sps_projectile", f"__{self.local_name}_proj_{self.tr_next_projectile_id}", proj_data)
            self.tr_fire_colldown = time.perf_counter()

            self.tr_next_projectile_id += 1

    def _dr_navigate(self, target_pos: Vec3) -> None:
        rand_scalar = 1.
        current_pos = self.ai_trans._pos

        for i in range(self.DRONE_NAVIG_MAX_ATTEMPTS):
            nav_target_pos = Vec3(target_pos) + Vec3(random.uniform(-1.2, 1.2), random.uniform(.2, 1.2), random.uniform(-1.2, 1.2)).elementwise() * rand_scalar

            if nav_target_pos != current_pos:
                vis_ray = PhysRay.make(current_pos, (nav_target_pos - current_pos).normalize(), self.ai_hitbox_size)
                vis_hit = GameState.collider_scene.first_hit(vis_ray, (nav_target_pos - current_pos).length())

                if vis_hit is not None:
                    # rand_scalar /= 1.6
                    continue # nav_target_pos not reachable, retry

            self.dr_nav_target_pos = nav_target_pos
            return

        pass # TODO: tiny graph pathfinder over nodes

    def _dr_check_collisions_and_apply_velocity(self) -> None:
        # tbh this comes derectly from PlayerMovement, only modified to for the SpsHitboxAi class

        dt = GameState.delta_time
        pos = Vec3(self.ai_trans._pos)
        vel = self.dr_vel

        if vel.length_squared() != 0.:
            tmax = vel.length() * dt

            player_box: PhysRay = PhysRay.make(pos, vel.normalize(), self.ai_hitbox_size)
            scene_hit = GameState.collider_scene.first_hit(player_box, tmax)

            while scene_hit is not None:
                frac_traveled = scene_hit.tmin / tmax

                pos += vel * dt * frac_traveled
                vel = vel - vel.project(scene_hit.norm)
                dt *= 1. - frac_traveled

                # add a tiny nudge away from the collider to fully escape the hit 
                pos += scene_hit.norm * EPSILON

                if scene_hit.tout < 0.:
                    # we're stuck inside a collider (?)
                    # vel = Vec3()
                    # print("stuck", scene_hit.tout)
                    break

                # recalc scene hits
                tmax = vel.length() * dt
                if tmax != 0.:
                    player_box: PhysRay = PhysRay.make(pos, vel.normalize(), self.ai_hitbox_size)
                    scene_hit = GameState.collider_scene.first_hit(player_box, tmax)
                else:
                    break

            pos += vel * dt

        self.dr_vel = vel
        self.ai_trans.set_pos(pos)
        self.ai_hitbox.update(pos, self.ai_hitbox_size)

    def tick_enemy_drone(self) -> None:
        # check for player visibility

        if SpsState.p_health != 0:

            target_dir = (SpsState.p_active_controller.p_pos - self.ai_fire_pos + Vec3(0., SpsState.p_active_controller.PLAYER_SIZE.y / 2, 0.))
            target_dist = target_dir.length()

            if target_dist == 0.:
                return # both target and origin are at the same place, possible crash, just give up

            target_dir.normalize_ip()

            vis_ray = PhysRay.make(self.ai_fire_pos, target_dir)
            vis_hit = GameState.collider_scene.first_hit(vis_ray, target_dist)

            is_visible = vis_hit is None
        else:
            is_visible = False

        if is_visible:
            self.ai_agro_level = 100.
            self.ai_target_last_seen_pos = Vec3(SpsState.p_active_controller.p_pos)
            self.ai_target_last_seen_time = time.perf_counter()

        else:
            self.ai_agro_level = max(0., self.ai_agro_level - self.AI_ARGO_DECAY * GameState.delta_time)

        # set travel target pos

        if (self.dr_nav_target_pos - self.ai_trans._pos).length_squared() < self.DRONE_NAVIG_TARGET_MARGIN ** 2 or self.dr_stuck: # retarget when arrived at target
            if GameState.current_time - self.dr_nav_margin_cooldown > self.DRONE_NAVIG_NEXT_TARGET_COOLDOWN: # retarget only after some time near the target
                # TODO: visible target pos when no-approaching (as by ai_manager) 

                if is_visible:
                    # override target_pos even when mid navigation if players visible
                    self._dr_navigate(SpsState.p_active_controller.p_pos)

                elif self.ai_agro_level > 0.:
                    self._dr_navigate(self.ai_target_last_seen_pos)

                else:
                    pass # TODO: patrol, choose a navnode to move to

            idling_at_target = True
        else:
            self.dr_nav_margin_cooldown = GameState.current_time
            idling_at_target = False

        # stuck detection

        if self.dr_vel.length_squared() > .05 or idling_at_target:
            self.dr_last_non_stuck_time = GameState.current_time
            self.dr_stuck = False

        if GameState.current_time - self.dr_last_non_stuck_time > self.DRONE_NAVIG_MAX_STUCK_TIME:
            self.dr_stuck = True

        # tick travel update

        target_diff = self.dr_nav_target_pos - self.ai_trans._pos

        import math
        try: nav_target_vel: Vec3 = target_diff.normalize() * min(self.DRONE_NAVIG_SPEED, math.exp(target_diff.length()) - .6)
        except: nav_target_vel = Vec3()

        try: nav_accel: Vec3 = ((nav_target_vel - self.dr_vel) * self.DRONE_NAVIG_ACCEL).clamp_magnitude(self.DRONE_NAVIG_SPEED)
        except: nav_accel = Vec3()

        self.dr_vel += (nav_accel * GameState.delta_time)
        self._dr_check_collisions_and_apply_velocity()

        # debug gizmos

        if SpsState.cheat_ai_debug:
            # gizmo.draw_text(self.ai_trans._pos, f"ai_type: {self.ai_type}\nai_argo_level: {round(self.ai_agro_level, 2)}\nai_vis: {is_visible}\ndr_nav_target_pos: {self.dr_nav_target_pos}", start_fade=float('inf'))

            line_col = Vec3(.35, 1., 1.)
            gizmo.draw_line(self.dr_nav_target_pos + Vec3(.1, .0, .0), self.dr_nav_target_pos - Vec3(.1, .0, .0), line_col, line_col)
            gizmo.draw_line(self.dr_nav_target_pos + Vec3(.0, .1, .0), self.dr_nav_target_pos - Vec3(.0, .1, .0), line_col, line_col)
            gizmo.draw_line(self.dr_nav_target_pos + Vec3(.0, .0, .1), self.dr_nav_target_pos - Vec3(.0, .0, .1), line_col, line_col)

            gizmo.draw_line(self.ai_trans._pos, self.ai_trans._pos + nav_accel, Vec3(1., 0., 0.), Vec3(1., 0., 0.))
            gizmo.draw_line(self.ai_trans._pos, self.ai_trans._pos + self.dr_vel, Vec3(1., 0., 1.), Vec3(1., 0., 1.))

            if self.ai_agro_level > 0.:
                gizmo.draw_box(self.ai_target_last_seen_pos - Vec3(.2, .2, .2), self.ai_target_last_seen_pos + Vec3(.2, .2, .2), Vec3(.35, 1., 1.))

    # == entity hooks ==

    @staticmethod
    def spawn(en_data: dict) -> 'SpsHitboxAi':
        return SpsHitboxAi(en_data)

    def despawn(self) -> None:
        self.ai_model.hide()
        SpsState.hitbox_scene.remove_coll(self.ai_hitbox)

    @staticmethod
    def dev_tick(s: dict | None, dev_state: en.DevTickState, en_data: dict) -> dict:
        # validate entity data

        if not en_data["ai_type"] in SpsHitboxAi.AI_TYPE_TABLE:
            raise KeyError("unknown ai_type")
        
        # init dev state

        if s is None:
            if en_data["t_pos"] is None:
                en_data["t_pos"] = dev_state.suggested_initial_pos

            s = {"mesh": BtStaticMesh(en_data), "en_data": dict(en_data)}
        elif en_data != s["en_data"]:
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

            # it's just editor preview ui, performance police please it's 11pm...
            fire_pos = Vec3(*(s["mesh"].mesh_trans._trans_matrix @ np.array([*en_data["ai_fire_offset"], 1.], dtype=np.float32))[0:3])
            line_col = Vec3(1., 1., .35)

            gizmo.draw_line(fire_pos + Vec3(.1, .0, .0), fire_pos - Vec3(.1, .0, .0), line_col, line_col)
            gizmo.draw_line(fire_pos + Vec3(.0, .1, .0), fire_pos - Vec3(.0, .1, .0), line_col, line_col)
            gizmo.draw_line(fire_pos + Vec3(.0, .0, .1), fire_pos - Vec3(.0, .0, .1), line_col, line_col)

        return s

    hitbox_health: int

    # which ai is used for this entity
    # - 0 - enemy_turret
    # - 1 - enemy_drone
    ai_type: int

    ai_trans: Transform
    ai_model: ModelRenderer

    ai_hitbox_size: Vec3
    ai_hitbox: PhysAABB
    ai_fire_offset: np.ndarray # a np vec4 ready to be matmultiplied with the transform matrix
    ai_fire_pos: Vec3

    ai_agro_level: float
    ai_target_last_seen_pos: Vec3
    ai_target_last_seen_time: float

    # turret vars

    tr_view_dir: Vec3
    tr_state: int

    tr_prefire_pause: float
    tr_fire_colldown: float
    tr_next_projectile_id: int

    tr_scan_cooldown: float
    tr_scan_target_dir: Vec3

    tr_initial_view_dir: Vec3
    dr_last_non_stuck_time: float
    dr_stuck: bool

    local_name: str | None

    # drone vars

    dr_vel: Vec3

    dr_nav_target_pos: Vec3 # current nav target
    dr_nav_nodes_to_travel: list[int] # nav nodes in a queue to nav to the desired pos
    dr_nav_margin_cooldown: float

def gen_def_data() -> dict:
    return {
        "t_pos": None,
        "t_rot": Vec3(0.0, 0.0, 0.0),
        "t_scale": Vec3(1.0, 1.0, 1.0),
        "ai_type": "enemy_turret",
        "ai_fire_offset": Vec3(0.0, 0.0, -.5),
        "hitbox_scale": Vec3(1.0, 1.0, 1.0),
        "hitbox_health": 120,
        "a_model_mesh": "models/icosph.npz",
        "a_model_vshader": "shaders/base_cam.vert",
        "a_model_fshader": "shaders/unlit.frag",
        "a_model_albedo": "textures/def_white.png",
        "a_model_transparent": False,
        "a_model_uniforms": {},
    }

en.create_entity_type("sps_hitbox_ai", SpsHitboxAi.spawn, SpsHitboxAi.despawn, SpsHitboxAi.dev_tick, gen_def_data)