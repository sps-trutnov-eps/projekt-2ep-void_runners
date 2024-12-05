from dataclasses import dataclass
import random

from engine.cue.cue_state import GameState
from engine.cue.phys.cue_phys_types import PhysAABB, PhysRay
from engine.cue.rendering import cue_gizmos as gizmo
from engine.cue.rendering.cue_resources import GPUMesh
from engine.cue.components.cue_transform import Transform
from engine.cue.components.cue_model import ModelRenderer

from components.line_renderer import LineRenderer
from sps_state import SpsState
import prefabs

from pygame.math import Vector3 as Vec3
import pygame as pg
import numpy as np
from OpenGL import GL as gl

# == glock 19 ==

@dataclass(init=False, slots=True)
class GlockImpl:
    def __init__(self):
        prefabs.spawn_prefab_from_file("p_view_model", "prefabs/view_models/glock_19.json")
        SpsState.p_hud_view_mesh = GameState.entity_storage.get_entity("sps_view_mesh", "p_view_model")
        self.view_initial_pos = SpsState.p_hud_view_mesh.view_space_trans._pos

        self.fire_cooldown = 0.
        self.view_knockback = Vec3()

        SpsState.p_ammo_regen_cooldown = 0

        self.beam_prefab = {
            "a_model_mesh": "models/crate.npz",
            "a_model_vshader": "shaders/line_segment.vert",
            "a_model_fshader": "shaders/emit_surf.frag",
            "a_model_albedo": "textures/def_white.png",
            "a_model_transparent": True,
            "a_model_uniforms": {
                "emit_power": 1.,
            },
        }
        self.active_beam_models = []

    def _new_beam(self, origin: Vec3, end: Vec3) -> None:
        # gen model

        beam_mesh = GPUMesh()
        beam_dir = (end - origin).normalize()

        vert_buf = np.array([*origin, *origin, *end, *end], dtype=np.float32)
        norm_buf = np.array([*beam_dir, *beam_dir, *beam_dir, *beam_dir], dtype=np.float32)
        uv_buf = np.array([0., 0., 0., 1., 1., 0., 1., 1.], dtype=np.float32)

        elem_buf = np.array([0, 1, 2, 2, 1, 3], dtype=np.uint32)

        beam_mesh.write_to(vert_buf, norm_buf, uv_buf, 4, elem_buf, 6, gl.GL_DYNAMIC_DRAW)

        # init renderer

        # beam_model = LineRenderer(self.beam_prefab, beam_mesh, .05, Transform(origin + (end - origin) * .5, Vec3()))
        # self.active_beam_models.append((GameState.current_time, beam_model))

        beam_model = LineRenderer(self.beam_prefab, beam_mesh, .02, Transform(origin + (end - origin) * .5, Vec3()))
        self.active_beam_models.append((GameState.current_time, beam_model))

    @np.errstate(all='ignore')
    def tick(self):
        mb = pg.mouse.get_pressed()

        # process fire input

        if mb[0] and GameState.current_time - self.fire_cooldown > .05 and SpsState.p_ammo > 0:
            # modify inter-frame state

            self.fire_cooldown = GameState.current_time
            self.view_knockback = Vec3(0., 0., .2)
            
            SpsState.p_ammo -= 1
            SpsState.p_ammo_regen_cooldown = GameState.current_time + 2.

            # hit scan and damage

            forward_dir = SpsState.p_active_controller.view_forward

            fire_pos = SpsState.p_active_controller.p_pos + SpsState.p_active_controller.CAMERA_OFFSET
            fire_pos += forward_dir * (min(abs(SpsState.p_active_controller.PLAYER_SIZE.x / np.float32(forward_dir.x)), abs(SpsState.p_active_controller.PLAYER_SIZE.y / np.float32(forward_dir.y)), abs(SpsState.p_active_controller.PLAYER_SIZE.z / np.float32(forward_dir.z)))) # converting to np.float32 to make div by zero a "valid" operation

            fire_ray = PhysRay.make(fire_pos, SpsState.p_active_controller.view_forward)

            coll_hit = GameState.collider_scene.first_hit(fire_ray)
            box_hit = SpsState.hitbox_scene.first_hit(fire_ray, float('inf') if coll_hit is None else coll_hit.tmin)

            if box_hit is not None:
                hit_pos = Vec3(*box_hit.pos)
                box_hit.usr.on_damage(1000., hit_pos)

            elif coll_hit is not None:
                hit_pos = Vec3(*coll_hit.pos)

            else:
                hit_pos = fire_pos + forward_dir * 1000.

            # spawn visual beam

            # TODO: get beam origin from view models space
            origin = Vec3(*(SpsState.p_hud_view_mesh.view_space_trans._trans_matrix @ np.array([0., -.8, .8, 1.], dtype=np.float32))[0:3])

            self._new_beam(origin, hit_pos)

        # reload ammo when valid

        if SpsState.p_ammo < 100 and GameState.current_time > SpsState.p_ammo_regen_cooldown:
            SpsState.p_ammo = min(100, SpsState.p_ammo + 2)
            SpsState.p_ammo_regen_cooldown = GameState.current_time

        # update view model

        self.view_knockback /= 1. + (20. * GameState.delta_time)
        SpsState.p_hud_view_mesh.view_space_trans.set_pos(self.view_initial_pos + self.view_knockback)

        # update beam models

        to_remove = []
        for i, beam in enumerate(self.active_beam_models):
            spawn_time, m = beam
            
            lifetime = 1. - (GameState.current_time - spawn_time)
            m.shader_uniform_data[2].bind_value = lifetime * 5.

            if lifetime < 0.:
                m.despawn()
                to_remove.append(i)

        for offset, i in enumerate(to_remove):
            self.active_beam_models.pop(i - offset)

    view_initial_pos: Vec3
    view_knockback: Vec3
    fire_cooldown: float

    beam_model: ModelRenderer

    active_beam_models: list[tuple[float, LineRenderer]]
    beam_prefab: dict

# == fdev ==

@dataclass(init=False, slots=True)
class FdevImpl:
    def __init__(self):
        prefabs.spawn_prefab_from_file("p_view_model", "prefabs/view_models/glock_19.json")
        SpsState.p_hud_view_mesh = GameState.entity_storage.get_entity("sps_view_mesh", "p_view_model")
        self.view_initial_pos = SpsState.p_hud_view_mesh.view_space_trans._pos

        self.view_knockback = Vec3()
        SpsState.p_ammo_regen_cooldown = 0

    @np.errstate(all='ignore')
    def tick(self):
        mb = pg.mouse.get_pressed()

        # process fire input

        if (mb[0] or mb[2]) and SpsState.p_ammo > 0:
            # modify inter-frame state

            self.view_knockback = Vec3(random.uniform(-.005, .005), random.uniform(-.005, .005), .2 + random.uniform(-.01, .01))
            
            SpsState.p_ammo -= 1
            SpsState.p_ammo_regen_cooldown = GameState.current_time + 2.

            # hit scan and damage

            forward_dir = SpsState.p_active_controller.view_forward

            fire_pos = SpsState.p_active_controller.p_pos + SpsState.p_active_controller.CAMERA_OFFSET
            fire_pos += forward_dir * (min(abs((SpsState.p_active_controller.PLAYER_SIZE.x + .5) / np.float32(forward_dir.x)), abs((SpsState.p_active_controller.PLAYER_SIZE.y + .5) / np.float32(forward_dir.y)), abs((SpsState.p_active_controller.PLAYER_SIZE.z + .5) / np.float32(forward_dir.z)))) # converting to np.float32 to make div by zero a "valid" operation

            coll_test_ray = PhysRay.make(fire_pos, SpsState.p_active_controller.view_forward, Vec3(.2, .2, .2))
            fire_ray = PhysRay.make(fire_pos, SpsState.p_active_controller.view_forward, Vec3(1., 1., 1.))

            coll_hit = GameState.collider_scene.first_hit(coll_test_ray)
            box_hits = SpsState.hitbox_scene.all_hits(fire_ray, float('inf') if coll_hit is None else coll_hit.tmin)

            push_mode = mb[0]

            # apply force to hits
            for hit in box_hits:
                hit.usr.on_force(forward_dir * 50. if push_mode else (fire_pos - Vec3(*hit.pos)).normalize() * 35.)

            # apply reverse force to player
            SpsState.p_active_controller.p_vel += (-forward_dir * 3. if push_mode else forward_dir * 2.) * GameState.delta_time

        # reload ammo when valid

        if SpsState.p_ammo < 250 and GameState.current_time > SpsState.p_ammo_regen_cooldown:
            SpsState.p_ammo += 5
            SpsState.p_ammo_regen_cooldown = GameState.current_time + .05

        # update view model

        self.view_knockback /= 1. + (20. * GameState.delta_time)
        SpsState.p_hud_view_mesh.view_space_trans.set_pos(self.view_initial_pos + self.view_knockback)

    view_initial_pos: Vec3
    view_knockback: Vec3
    fire_cooldown: float