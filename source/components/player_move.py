from dataclasses import dataclass
import math

from engine.cue.cue_state import GameState
from engine.cue.components.cue_transform import Transform
from engine.cue.rendering.cue_camera import Camera

import engine.cue.cue_sequence as seq

from pygame.math import Vector3 as Vec3, Vector2 as Vec2
import pygame as pg

from engine.cue import cue_utils as utils
import imgui

# The core player movement controller for SPSU

@dataclass(init=False, slots=True)
class PlayerMovement:
    # *_MAX_SPEED - player won't accelerate past this speed
    # *_ACCEL - how fast will player change its velocity (in units per second)
    # *_IMPULSE - a one time velotity impulse (immidiate, not per second)

    WALK_MAX_SPEED = 1.6
    WALK_ACCEL = 16
    SPRINT_MAX_SPEED = 3.6
    SPRINT_ACCEL = 24
    AIR_ACCEL = .4
    MOUSE_ACCEL = .2 # (degrees per mouse-specific unit)

    JUMP_IMPULSE = Vec3(0., 2.5, 0.)
    JUMP_FORWARD_IMPULSE = .6

    GROUND_FRICTION = 16
    OVERSPEED_FRICTION = 2
    GRAVITY = Vec3(0., -5.6, 0.)

    PLAYER_SIZE = Vec3(.2, .95, .2)
    CAMERA_OFFSET = Vec3(0, .8, 0)

    def __init__(self, player_trans: Transform, player_cam: Camera, initial_view_rot: Vec2 = Vec2(0, 0)) -> None:
        self.controlled_trans = player_trans
        self.controlled_cam = player_cam
        self.set_captured(True) # by-default true

        self.p_pos = Vec3(player_trans._pos)
        self.p_vel = Vec3(0, 0, 0)
        self.p_state = 0

        self.view_rot = initial_view_rot
        self.show_player_info = False

        seq.next(PlayerMovement.tick, self)

    def tick(self) -> None:
        # call the specific player controller for the current state

        if self.p_state == 0: # on ground / landed
            self.tick_landed()
        
        elif self.p_state == 1: # in air / in-flight
            self.tick_in_flight()

        # update controlled transform

        if self.is_captured:
            # mouse input
            rel = pg.mouse.get_rel()
            self.view_rot.x += rel[1] * PlayerMovement.MOUSE_ACCEL
            self.view_rot.y -= rel[0] * PlayerMovement.MOUSE_ACCEL

            res = GameState.renderer.win_res
            pg.mouse.set_pos(res[0] // 2, res[1] // 2)

        yaw_rot, pitch_rot = self.view_rot.yx
        yaw_rot = math.radians(yaw_rot)
        pitch_rot = math.radians(pitch_rot)

        self.view_forward = -Vec3(math.sin(yaw_rot) * math.cos(pitch_rot), math.sin(pitch_rot), math.cos(yaw_rot) * math.cos(pitch_rot))
        self.view_forward_flat = -Vec3(math.sin(yaw_rot), 0., math.cos(yaw_rot))
        self.view_right_flat = -Vec3(-math.cos(yaw_rot), 0., math.sin(yaw_rot))

        self.controlled_trans.set_pos(self.p_pos)
        self.controlled_trans.set_rot(Vec3(self.view_rot[0], self.view_rot[1], 0.))

        self.controlled_cam.set_view(self.p_pos + PlayerMovement.CAMERA_OFFSET, Vec3(self.view_rot[0], self.view_rot[1], 0.))

        if self.show_player_info:
            GameState.renderer.fullscreen_imgui_ctx.set_as_current_context()

            with utils.begin_dev_overlay("player_info"):
                imgui.text(f"p_state: {self.p_state}")
                imgui.text(f"p_pos: {round(self.p_pos.x, 4)} {round(self.p_pos.y, 4)} {round(self.p_pos.z, 4)}")
                imgui.text(f"p_vel: {round(self.p_vel.x, 4)} {round(self.p_vel.y, 4)} {round(self.p_vel.z, 4)}")
                imgui.text(f"view_rot: {round(self.view_rot.x, 4)} {round(self.view_rot.y, 4)}")

        seq.next(PlayerMovement.tick, self)

    # == landed state player movement ==
    # note: do not search for any kind of logic here, most stuff was figured out by feel and experimentation

    def land_accel_func(self, d: Vec3, vel: Vec3, maxs: float, accel: float, dt: float) -> Vec3:
        return d * ((maxs - vel.length() * .0) / maxs * accel) * dt

    def tick_landed(self) -> None:
        dt = GameState.delta_time

        # update user input

        input_active = False

        if self.is_captured:
            keys = pg.key.get_pressed()
            mods = pg.key.get_mods()
            vel = self.p_vel

            # jump and change state
            if keys[pg.K_SPACE]:
                input_active = True

                self.p_vel += (self.view_forward_flat * PlayerMovement.JUMP_FORWARD_IMPULSE * (0.)) + PlayerMovement.JUMP_IMPULSE
                self.p_state = 1

                self.tick_in_flight()
                return

            if mods & pg.KMOD_SHIFT:
                max_speed = PlayerMovement.SPRINT_MAX_SPEED
                accel = PlayerMovement.SPRINT_ACCEL
            else:
                max_speed = PlayerMovement.WALK_MAX_SPEED
                accel = PlayerMovement.WALK_ACCEL

            accel_vec = Vec3(0, 0, 0)

            if keys[pg.K_w]:
                accel_vec += self.land_accel_func(self.view_forward_flat, vel, max_speed, accel, dt)
                input_active = True
            if keys[pg.K_s]:
                accel_vec -= self.land_accel_func(self.view_forward_flat, vel, max_speed, accel, dt)
                input_active = True
            if keys[pg.K_d]:
                accel_vec += self.land_accel_func(self.view_right_flat, vel, max_speed, accel, dt)
                input_active = True
            if keys[pg.K_a]:
                accel_vec -= self.land_accel_func(self.view_right_flat, vel, max_speed, accel, dt)
                input_active = True

            # vel over max speed friction
            vel /= 1. + vel.length() / max_speed * PlayerMovement.OVERSPEED_FRICTION * dt

            # add accel to vel and reclamp to max or current speed (allows changing dir even at max speed, doesn't over accelerate and allows control even when over max speed eg. when landing from air or sprint)
            u_vel = vel + accel_vec
            u_vel /= max(u_vel.length() / max(vel.length(), max_speed), 1.0)

            self.p_vel = u_vel

        # update (always) ticking state

        if not input_active:
            self.p_vel /= 1. + PlayerMovement.GROUND_FRICTION * dt
            
        pos_diff: Vec3 = self.p_vel * dt
        scene_hit = None #PhysGrid.slide_aabb(self.p_pos, pos_diff)

        if scene_hit is None:
            self.p_pos += pos_diff
        else:
            pass # TODO: phys collision

    def tick_in_flight(self) -> None:
        dt = GameState.delta_time

        # update user input

        input_active = False

        if self.is_captured:
            keys = pg.key.get_pressed()
            mods = pg.key.get_mods()
            vel = self.p_vel

            accel = PlayerMovement.AIR_ACCEL
            accel_vec = Vec3(0, 0, 0)

            if keys[pg.K_w]:
                accel_vec += self.view_forward_flat * accel * dt
                input_active = True
            if keys[pg.K_s]:
                accel_vec -= self.view_forward_flat * accel * dt
                input_active = True
            if keys[pg.K_d]:
                accel_vec += self.view_right_flat * accel * dt
                input_active = True
            if keys[pg.K_a]:
                accel_vec -= self.view_right_flat * accel * dt
                input_active = True

            vel += accel_vec

        # update (always) ticking state

        self.p_vel += PlayerMovement.GRAVITY * dt
            
        pos_diff: Vec3 = self.p_vel * dt
        scene_hit = None #PhysGrid.slide_aabb(self.p_pos, pos_diff)

        if scene_hit is None:
            self.p_pos += pos_diff
        else:
            pass # TODO: phys collision

        # check if landed and change state (temp. currently assume infinite floor at y == 0.)
        if self.p_pos.y <= 0.:
            self.p_vel.y = 0.
            self.p_state = 0

    def set_captured(self, cap: bool) -> None:
        pg.event.set_grab(cap)
        pg.mouse.set_visible(not cap)

        self.is_captured = cap

    controlled_trans: Transform
    controlled_cam: Camera
    is_captured: bool # does controller have control of the inputs

    p_pos: Vec3
    p_vel: Vec3
    
    # player state:
    #  0 - on gound / landed
    #  1 - in air / in-flight
    p_state: int

    view_rot: Vec2
    view_forward: Vec3
    view_forward_flat: Vec3 # same as [view_forward] but with y ignored and normalized
    view_right_flat: Vec3

    p_aabb: None

    # debug
    show_player_info: bool