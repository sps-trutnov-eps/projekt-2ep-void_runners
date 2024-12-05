import time, random, math

from dataclasses import dataclass
from engine.cue.entities import cue_entity_types as en
from engine.cue import cue_sequence as seq
from engine.cue.cue_state import GameState

from engine.cue.entities.cue_entity_utils import handle_transform_edit_mode
from engine.cue.rendering import cue_gizmos as gizmo

from engine.cue.entities.bt_static_mesh import BtStaticMesh
from engine.cue.components.cue_transform import Transform
from engine.cue.components.cue_model import ModelRenderer
from engine.cue.rendering.cue_resources import GPUMesh
from engine.cue.phys.cue_phys_types import PhysAABB, PhysRay, EPSILON

from components.line_renderer import LineRenderer
from sps_state import SpsState
import prefabs

from pygame.math import Vector3 as Vec3
from OpenGL import GL as gl
import numpy as np

# a semi-generic entity for most ai controlled enemies or npcs

@dataclass(init=False, slots=True)
class SpsHitboxAi:
    AI_TYPE_TABLE = {
        "enemy_turret": 0,
        "enemy_drone": 1,
    }
    AI_ARGO_DECAY = 12.
    AI_UPDATE_RATE = 5 # in updates per second

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

    DRONE_NAVIG_PLAYER_AVOIDANCE = 15. # how much to avoid flying into the player

    def __init__(self, en_data: dict) -> None:
        self.hitbox_health = en_data["hitbox_health"]
        self.ai_type = self.AI_TYPE_TABLE[en_data["ai_type"]]

        self.ai_trans = Transform(en_data["t_pos"], en_data["t_rot"], en_data["t_scale"])
        self.ai_model = ModelRenderer(en_data, self.ai_trans)

        self.ai_fire_offset = np.array([*en_data["ai_fire_offset"], 1.], dtype=np.float32)
        self.ai_fire_pos = Vec3(*(self.ai_trans._trans_matrix @ self.ai_fire_offset)[0:3]) # initial, updated in tick
        self.ai_hitbox_size = self.ai_trans._scale.elementwise() * en_data["hitbox_scale"]
        self.ai_hitbox = PhysAABB.make(self.ai_trans._pos, self.ai_hitbox_size, self)
        SpsState.hitbox_scene.add_coll(self.ai_hitbox)

        self.ai_agro_level = 0.
        self.ai_target_last_seen_pos = Vec3()
        self.ai_target_last_seen_time = 0.
        self.ai_overlay_rot = en_data["t_rot"]
        self.ai_last_update = GameState.current_time

        if self.ai_type == 0:
            self.tr_initial_view_dir = Vec3(0., 0., 1.)
            self.tr_view_dir = Vec3(self.tr_initial_view_dir)
            self.tr_view_target_dir = Vec3(self.tr_initial_view_dir)
            self.tr_state = 0

            self.tr_fire_colldown = 0
            self.tr_next_projectile_id = 0

            self.tr_prefire_pause = GameState.current_time
            self.tr_laser_length = 0.

            self.tr_laser_mesh = GPUMesh()
            self._tr_gen_laser_mesh()

            laser_data = {
                "a_model_vshader": "shaders/line_segment.vert",
                "a_model_fshader": "shaders/unlit.frag",
                "a_model_albedo": "textures/def_white.png",
                "a_model_transparent": True,
            }

            # note: using ai transform which may be far from the laser mesh itself, this may cause wrong draw ordering and transparency artifacts but good enough
            self.tr_laser_renderer = LineRenderer(laser_data, self.tr_laser_mesh, .008, self.ai_trans)

            # temporally space out ai updates over many frames, so only a few updates per frame happen
            seq.after(random.uniform(0., .5), self.update_ai_enemy_turret)
        
        elif self.ai_type == 1:
            self.dr_vel = Vec3()

            self.dr_nav_nodes_to_travel = []
            self.dr_nav_target_pos = en_data["t_pos"]
            self.dr_nav_target_is_player = False
            self.dr_nav_margin_cooldown = GameState.current_time

            self.dr_last_non_stuck_time = GameState.current_time
            self.dr_stuck = False

            seq.after(random.uniform(0., .5), self.update_ai_enemy_drone)
        
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
            return # entity despawned already, this case should be unreachable, but it happens anyway... 

        if self.hitbox_health <= 0:
            # TODO: spawn particle debris

            GameState.entity_storage.despawn(self.local_name)
            self.local_name = None

        try:
            hit_dir = (hit_pos - self.ai_trans._pos).normalize()
            # TODO: pong view_dir a lil up on damage

        except:
            pass # malformed hit pos (hit_pos == self.ai_trans._pos), just ignore

    def on_force(self, active_force: Vec3) -> None:
        if self.ai_type == 1:
            self.dr_vel += active_force * GameState.delta_time

    # == ai impls ==

    def _tr_gen_laser_mesh(self) -> None:
        laser_end_pos = (self.ai_fire_pos + (self.tr_view_dir.elementwise() * self.tr_laser_length))

        vert_buf = np.array([*self.ai_fire_pos, *self.ai_fire_pos, *laser_end_pos, *laser_end_pos], dtype=np.float32)
        norm_buf = np.array([*self.tr_view_dir, *self.tr_view_dir, *self.tr_view_dir, *self.tr_view_dir], dtype=np.float32)
        uv_buf = np.array([0., 0., 0., 1., 1., 0., 1., 1.], dtype=np.float32)

        # vert_buf = np.array([0., .5, 0., 0., .5, 0., 1., .5, 0., 1., .5, 0.], dtype=np.float32)
        elem_buf = np.array([0, 1, 2, 2, 1, 3], dtype=np.uint32)

        self.tr_laser_mesh.write_to(vert_buf, norm_buf, uv_buf, 4, elem_buf, 6, gl.GL_STREAM_DRAW)

    def update_ai_enemy_turret(self) -> None:
        if self.local_name is None:
            return # despawned

        # check for player visibility
        
        if SpsState.p_health != 0 and not SpsState.cheat_ai_invis:

            target_dir = (SpsState.p_active_controller.p_pos - self.ai_fire_pos + Vec3(0., SpsState.p_active_controller.PLAYER_SIZE.y / 2, 0.))
            target_dist = target_dir.length()

            if target_dist == 0.:
                return # both target and origin are at the same place, possible crash, just give up

            target_dir.normalize_ip()

            vis_ray = PhysRay.make(self.ai_fire_pos, target_dir)
            vis_hit = GameState.collider_scene.first_hit(vis_ray, target_dist)

            is_visible = vis_hit is None

            if is_visible:
                self.tr_view_target_dir = target_dir
        else:
            is_visible = False

        if is_visible:
            self.ai_agro_level = 100.
            self.ai_target_last_seen_pos = Vec3(SpsState.p_active_controller.p_pos)
            self.ai_target_last_seen_time = time.perf_counter()

        else:
            self.ai_agro_level = max(0., self.ai_agro_level - self.AI_ARGO_DECAY * (GameState.current_time - self.ai_last_update))

        self.ai_last_update = GameState.current_time
        seq.after(1 / self.AI_UPDATE_RATE, self.update_ai_enemy_turret)

    def tick_enemy_turret(self) -> None:
        # debug gizmos

        if SpsState.cheat_ai_debug:
            # gizmo.draw_text(self.ai_trans._pos, f"ai_type: {self.ai_type}\nai_argo_level: {round(self.ai_agro_level, 2)}\nai_vis: {is_visible}\ntr_state: {self.tr_state}", start_fade=float('inf'))

            line_col = Vec3(.35, 1., .35) if self.tr_state == 3 else Vec3(.35, .35, 1.)
            gizmo.draw_line(self.ai_fire_pos, self.ai_fire_pos + self.tr_view_dir * self.tr_laser_length, line_col, line_col)

        # aim for player

        if self.ai_agro_level == 100.:
            # player visible, align with player

            # recalc the view_target for player to avoid jittering when following
            self.tr_view_target_dir = (SpsState.p_active_controller.p_pos - self.ai_fire_pos + Vec3(0., SpsState.p_active_controller.PLAYER_SIZE.y / 2, 0.))

            try: self.tr_view_target_dir.normalize_ip()
            except: pass

            view_diff = self.tr_view_target_dir - self.tr_view_dir
            if view_diff.length_squared() != 0.:
                self.tr_view_dir += view_diff.normalize() * min(view_diff.length(), self.TURRET_AIM_SPEED_FACTOR * GameState.delta_time)
            
            try: self.tr_view_dir.normalize_ip()
            except: pass # this case (view_dir == [0, 0, 0]) is *very* unlikely, but still possible

            if self.tr_view_dir.dot(self.tr_view_target_dir) >= self.TURRET_AIM_ALIGN_TOLERANCE:
                self.tr_state = 3
            else:
                self.tr_state = 2

            self.tr_scan_cooldown = 0

        elif self.ai_agro_level > 0.:
            # animate the turret scan with random movements around the last seen point
            if GameState.current_time - self.tr_scan_cooldown > self.TURRET_SCAN_COOLDOWN:
                self.tr_scan_cooldown = GameState.current_time
                self.tr_view_target_dir = ((self.ai_target_last_seen_pos - self.ai_trans._pos).normalize() + Vec3(random.uniform(-.35, .35), random.uniform(-.35, .35), random.uniform(-.35, .35))).normalize()

            # interpolate around that scan dir
            view_diff = self.tr_view_target_dir - self.tr_view_dir
            if view_diff.length_squared() != 0.:
                self.tr_view_dir += view_diff.normalize() * min(view_diff.length(), self.TURRET_SCAN_SPEED_FACTOR * GameState.delta_time)

            self.tr_state = 1

        else:
            view_diff = self.tr_initial_view_dir - self.tr_view_dir
            if view_diff.length_squared() != 0.:
                self.tr_view_dir += view_diff.normalize() * min(view_diff.length(), self.TURRET_SCAN_SPEED_FACTOR * GameState.delta_time)

            self.tr_state = 0
            self.tr_prefire_pause = GameState.current_time

        # regen laser with latest dir

        # costly per frame hit scan, but it's a sacrifice i'm willing to make...
        laser_ray = PhysRay.make(self.ai_fire_pos, self.tr_view_dir)
        laser_hit = GameState.collider_scene.first_hit(laser_ray)
        self.tr_laser_length = laser_hit.tmin if laser_hit is not None else 1000.

        self._tr_gen_laser_mesh()

        # rotate model by dir

        try:
            forward_dir = self.tr_view_dir
            forward_dir_flat = Vec3(forward_dir.x, 0., forward_dir.z).normalize()
        except:
            forward_dir_flat = Vec3(0., 0., 0.)

        # atan2, my beloved
        self.ai_trans.set_rot(Vec3(0., math.degrees(math.atan2(forward_dir_flat.z, forward_dir_flat.x)), 0.) + self.ai_overlay_rot)

        # fire if valid

        if (
            self.tr_state == 3 and # player visible
            time.perf_counter() - self.tr_fire_colldown > self.TURRET_FIRE_COOLDOWN and # no inter-bullet cooldown
            GameState.current_time - self.tr_prefire_pause > self.TURRET_AIM_FIRE_PAUSE # no prefire cooldown    
            ):

            # load bullet prefab
            proj_name = f"__{self.local_name}_proj_{self.tr_next_projectile_id}"
            proj_prefab = prefabs.load_prefab(proj_name, "prefabs/turret_bullet.json")

            # setup initial dynamic entity data
            proj_prefab[0][2]["t_pos"] = self.ai_fire_pos
            proj_prefab[0][2]["projectile_dir"] = Vec3(self.tr_view_dir)

            prefabs.spawn_prefab(proj_prefab)

            self.tr_fire_colldown = time.perf_counter()
            self.tr_next_projectile_id += 1

    def _dr_navigate(self, target_pos: Vec3, is_player: bool) -> None:
        rand_scalar = 1.
        current_pos = self.ai_trans._pos

        for i in range(self.DRONE_NAVIG_MAX_ATTEMPTS):
            if not is_player:
                nav_target_pos = Vec3(target_pos) + Vec3(random.uniform(-1.2, 1.2), random.uniform(.2, 1.2), random.uniform(-1.2, 1.2)).elementwise() * rand_scalar
            else:
                nav_target_pos = Vec3(target_pos) + Vec3(random.uniform(-2.2, 2.2), random.uniform(.2, 2.2), random.uniform(-2.2, 2.2)).elementwise() * rand_scalar

            if nav_target_pos != current_pos:
                # note: it's better if we check if target is reachable but the cost of multiple hit scans is not worth the micro-stutters, rely on stuck detection
                vis_ray = PhysRay.make(current_pos, (nav_target_pos - current_pos).normalize(), self.ai_hitbox_size)
                vis_hit = GameState.collider_scene.first_hit(vis_ray, (nav_target_pos - current_pos).length())
                
                if vis_hit is not None or (is_player and (nav_target_pos - target_pos).length_squared() < 2. ** 2):
                    # rand_scalar /= 1.6
                    continue # nav_target_pos not reachable or too close, retry

            self.dr_nav_target_pos = nav_target_pos
            self.dr_nav_target_is_player = is_player
            return

    def _dr_check_collisions_and_apply_velocity(self) -> None:
        # tbh this comes derectly from PlayerMovement, only modified to for the SpsHitboxAi class

        dt = GameState.delta_time
        pos = Vec3(self.ai_trans._pos)
        vel = self.dr_vel

        if vel.length_squared() != 0.:
            tmax = vel.length() * dt

            player_box: PhysRay = PhysRay.make(pos, vel.normalize(), self.ai_hitbox_size)
            scene_hit = GameState.collider_scene.first_hit(player_box, tmax)

            for i in range(32):
                if scene_hit is None:
                    break

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
        SpsState.hitbox_scene.update_coll(self.ai_hitbox)

    def update_ai_enemy_drone(self) -> None:
        if self.local_name is None:
            return # despawned

        # check for player visibility

        if SpsState.p_health != 0 and not SpsState.cheat_ai_invis:
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
            self.ai_agro_level = max(0., self.ai_agro_level - self.AI_ARGO_DECAY * (GameState.current_time - self.ai_last_update))

        # set travel target pos

        if (self.dr_nav_target_pos - self.ai_trans._pos).length_squared() < self.DRONE_NAVIG_TARGET_MARGIN ** 2 or self.dr_stuck: # retarget when arrived at target
            if GameState.current_time - self.dr_nav_margin_cooldown > self.DRONE_NAVIG_NEXT_TARGET_COOLDOWN: # retarget only after some time near the target
                # TODO: visible target pos when no-approaching (as by ai_manager) 

                if is_visible:
                    # override target_pos even when mid navigation if players visible
                    self._dr_navigate(SpsState.p_active_controller.p_pos, True)

                elif self.ai_agro_level > 0.:
                    self._dr_navigate(self.ai_target_last_seen_pos, False)

                else:
                    nodes_by_dist = sorted(SpsState.active_nav_nodes, key=lambda node: (node.node_pos - self.ai_trans._pos).length_squared())

                    if nodes_by_dist:
                        nodes_to_test = nodes_by_dist[:min(self.DRONE_NAVIG_MAX_ATTEMPTS, len(nodes_by_dist) - 1)]
                        random.shuffle(nodes_to_test)

                        target_node = None
                        for node in nodes_to_test:
                            # patrol with nav nodes

                            node_pos_diff = node.node_pos - self.ai_trans._pos

                            node_dist = node_pos_diff.length()
                            if node_dist < self.DRONE_NAVIG_TARGET_MARGIN:
                                continue # already on this nav node

                            vis_ray = PhysRay.make(self.ai_trans._pos, node_pos_diff.normalize())
                            vis_hit = GameState.collider_scene.first_hit(vis_ray, node_dist)

                            if vis_hit is None:
                                target_node = node
                                break

                        if target_node is not None:
                            self._dr_navigate(target_node.node_pos, False)

            idling_at_target = True
        else:
            self.dr_nav_margin_cooldown = GameState.current_time
            idling_at_target = False

        if is_visible and not self.dr_nav_target_is_player:
            # override target dir to player if seen
            self._dr_navigate(SpsState.p_active_controller.p_pos, True)

        # stuck detection

        if self.dr_vel.length_squared() > .05 or idling_at_target:
            self.dr_last_non_stuck_time = GameState.current_time
            self.dr_stuck = False

        if GameState.current_time - self.dr_last_non_stuck_time > self.DRONE_NAVIG_MAX_STUCK_TIME:
            self.dr_stuck = True

        self.ai_last_update = GameState.current_time
        seq.after(1 / self.AI_UPDATE_RATE, self.update_ai_enemy_drone)

    def tick_enemy_drone(self) -> None:
        # tick travel update

        target_diff = self.dr_nav_target_pos - self.ai_trans._pos

        try: nav_target_vel: Vec3 = target_diff.normalize() * min(self.DRONE_NAVIG_SPEED, math.exp(target_diff.length()) - .6)
        except: nav_target_vel = Vec3()

        # try to avoid flying into the players face
        player_diff = (self.ai_trans._pos - SpsState.p_active_controller.p_pos)
        player_repulsion = player_diff.normalize() * max(2. - player_diff.length(), 0.) * self.DRONE_NAVIG_PLAYER_AVOIDANCE

        try: nav_accel: Vec3 = ((nav_target_vel - self.dr_vel) * self.DRONE_NAVIG_ACCEL).clamp_magnitude(self.DRONE_NAVIG_SPEED) + player_repulsion
        except: nav_accel = Vec3()

        self.dr_vel += (nav_accel * GameState.delta_time)
        self._dr_check_collisions_and_apply_velocity()

        # rotate model by dir

        if self.ai_agro_level == 100.:
            target_diff = SpsState.p_active_controller.p_pos - self.ai_trans._pos

            try: forward_dir_flat = Vec3(target_diff.x, 0., target_diff.z).normalize()
            except: forward_dir_flat = Vec3(0., 0., 0.)

        else:
            try: forward_dir_flat = Vec3(self.dr_vel.x, 0., self.dr_vel.z).normalize()
            except: forward_dir_flat = Vec3(0., 0., 0.)
        
        self.ai_trans.set_rot(Vec3(0., math.degrees(math.atan2(forward_dir_flat.z, forward_dir_flat.x)), 0.) + self.ai_overlay_rot)

        # debug gizmos

        if SpsState.cheat_ai_debug:
            # gizmo.draw_text(self.ai_trans._pos, f"dr_target_pos: {self.dr_nav_target_pos} ({self.dr_nav_target_pos - self.ai_trans._pos})\n", start_fade=float('inf'))

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
        if self.ai_type == 0:
            self.tr_laser_renderer.despawn()
        self.ai_model.despawn()

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
    ai_overlay_rot: Vec3
    ai_fire_pos: Vec3

    ai_agro_level: float
    ai_target_last_seen_pos: Vec3
    ai_target_last_seen_time: float
    ai_last_update: float

    # turret vars

    tr_view_dir: Vec3
    tr_view_target_dir: Vec3
    tr_state: int

    tr_prefire_pause: float
    tr_laser_length: float
    tr_fire_colldown: float
    tr_next_projectile_id: int

    tr_scan_cooldown: float
    tr_initial_view_dir: Vec3

    tr_laser_renderer: LineRenderer
    tr_laser_mesh: GPUMesh

    # drone vars

    dr_vel: Vec3

    dr_nav_target_pos: Vec3 # current nav target
    dr_nav_target_is_player: bool
    dr_nav_nodes_to_travel: list[int] # nav nodes in a queue to nav to the desired pos
    dr_nav_margin_cooldown: float
    
    dr_stuck: bool
    dr_last_non_stuck_time: float

    local_name: str | None

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