from dataclasses import dataclass
import math

from engine.cue.cue_state import GameState
from engine.cue.components.cue_transform import Transform
from engine.cue.rendering.cue_camera import Camera

import engine.cue.cue_sequence as seq

from pygame.math import Vector3 as Vec3, Vector2 as Vec2
import pygame as pg

# The core player movement controller for SPSU

@dataclass(init=False, slots=True)
class PlayerMovement:
    WALK_ACCEL = 2.
    MOUSE_ACCEL = math.radians(.2)

    GROUND_FRICTION = 8

    def __init__(self, player_trans: Transform, player_cam: Camera) -> None:
        self.controlled_trans = player_trans
        self.controlled_cam = player_cam
        self.set_captured(True) # by-default true

        self.p_pos = Vec3(0, 0, 0)
        self.p_vel = Vec3(0, 0, 0)
        self.p_state = 0

        self.view_rot = Vec2(0, 0)

        seq.next(PlayerMovement.tick, self)

    def tick(self) -> None:
        # call the specific player controller for the current state

        if self.p_state == 0: # on ground / landed
            self.tick_landed()
        
        elif self.p_state == 1: # in air / in-flight
            self.tick_in_flight()

        # update controlled transform

        yaw_rot, pitch_rot = self.view_rot.yx
        self.view_forward = -Vec3(math.sin(yaw_rot) * math.cos(pitch_rot), math.sin(pitch_rot), math.cos(yaw_rot) * math.cos(pitch_rot))
        self.view_forward_flat = -Vec3(math.sin(yaw_rot), 0., math.cos(yaw_rot))
        self.view_right_flat = -Vec3(-math.cos(yaw_rot), 0., math.sin(yaw_rot))

        self.controlled_trans.set_pos(self.p_pos)
        self.controlled_trans.set_rot(Vec3(self.view_rot[0], self.view_rot[1], 0.))

        self.controlled_cam.set_view(self.p_pos, Vec3(self.view_rot[0], self.view_rot[1], 0.))

        seq.next(PlayerMovement.tick, self)

    def tick_landed(self) -> None:
        dt = GameState.delta_time

        # update user input

        if self.is_captured:
            keys = pg.key.get_pressed()

            if keys[pg.K_w]:
                self.p_vel += self.view_forward_flat * PlayerMovement.WALK_ACCEL * dt
            if keys[pg.K_s]:
                self.p_vel -= self.view_forward_flat * PlayerMovement.WALK_ACCEL * dt
            if keys[pg.K_d]:
                self.p_vel += self.view_right_flat * PlayerMovement.WALK_ACCEL * dt
            if keys[pg.K_a]:
                self.p_vel -= self.view_right_flat * PlayerMovement.WALK_ACCEL * dt

            rel = pg.mouse.get_rel()
            self.view_rot.x += rel[1] * PlayerMovement.MOUSE_ACCEL
            self.view_rot.y -= rel[0] * PlayerMovement.MOUSE_ACCEL

            res = GameState.renderer.win_res
            pg.mouse.set_pos(res[0] // 2, res[1] // 2)

        # update (always) ticking state

        self.p_vel /= 1. + (PlayerMovement.GROUND_FRICTION * dt)

        pos_diff: Vec3 = self.p_vel * dt
        scene_hit = None #PhysGrid.slide_aabb(self.p_pos, pos_diff)

        if scene_hit is None:
            self.p_pos += pos_diff
        else:
            pass # TODO: phys collision

    def tick_in_flight(self) -> None:
        raise NotImplementedError

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
