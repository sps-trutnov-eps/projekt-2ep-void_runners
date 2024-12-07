from dataclasses import dataclass
import random

from engine.cue.cue_state import GameState
from engine.cue.phys.cue_phys_types import PhysAABB, PhysRay
from engine.cue.rendering import cue_gizmos as gizmo
from engine.cue import cue_sequence as seq
from engine.cue.rendering.cue_resources import GPUMesh
from engine.cue.components.cue_transform import Transform

from components.line_renderer import LineRenderer
from components.particle_renderer import ParticleRenderer
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

    @staticmethod
    def _tick_beam_model(beam) -> None:
        spawn_time, m = beam
            
        lifetime = 1. - (GameState.current_time - spawn_time)
        m.shader_uniform_data[2].bind_value = lifetime * 5.

        if lifetime <= 0.:
            m.despawn()
            return

        seq.next(GlockImpl._tick_beam_model, beam)

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
        seq.next(GlockImpl._tick_beam_model, (GameState.current_time, beam_model))

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

            origin = Vec3(*(SpsState.p_hud_view_mesh.view_space_trans._trans_matrix @ np.array([0., -.8, .8, 1.], dtype=np.float32))[0:3])
            self._new_beam(origin, hit_pos)

        # reload ammo when valid

        if SpsState.p_ammo < 100 and GameState.current_time > SpsState.p_ammo_regen_cooldown:
            SpsState.p_ammo = min(100, SpsState.p_ammo + 2)
            SpsState.p_ammo_regen_cooldown = GameState.current_time

        # update view model

        self.view_knockback /= 1. + (20. * GameState.delta_time)
        SpsState.p_hud_view_mesh.view_space_trans.set_pos(self.view_initial_pos + self.view_knockback)

    view_initial_pos: Vec3
    view_knockback: Vec3
    fire_cooldown: float

    beam_prefab: dict

# == flamethrower

@dataclass(init=False, slots=True)
class FlameImpl:
    def __init__(self) -> None:
        prefabs.spawn_prefab_from_file("p_view_model", "prefabs/view_models/glock_19.json")
        SpsState.p_hud_view_mesh = GameState.entity_storage.get_entity("sps_view_mesh", "p_view_model")
        self.view_initial_pos = SpsState.p_hud_view_mesh.view_space_trans._pos

        self.view_knockback = Vec3()
        SpsState.p_ammo_regen_cooldown = 0

        self.fire_p_pos = []
        self.fire_p_vel = []
        self.fire_p_spawn_time = []

        self.fire_point_mesh = GPUMesh()
        self.fire_point_trans = Transform(Vec3(), Vec3()) # used for non_opaque sorting
        self.fire_point_lifetime_buf = gl.glGenBuffers(1)

        fire_data = {
            "a_model_mesh": self.fire_point_mesh,
            "a_model_vshader": "shaders/flame.vert",
            "a_model_fshader": "shaders/flame_quad.frag",
            "a_model_transparent": True,
            "a_model_albedo": "textures/fireSheet.png"
        }
        self.fire_point_renderer = ParticleRenderer(fire_data, self.fire_point_mesh, self.fire_point_trans)
        gl.glEnable(gl.GL_PROGRAM_POINT_SIZE)

        seq.next(self._update_point_mesh)

    def _update_point_mesh(self) -> None:
        # update particle system

        to_remove = []
        point_data = []
        lifetime_data = []

        avg_pos = Vec3()

        for i in range(len(self.fire_p_pos)):
            lf = 5. - (GameState.current_time - self.fire_p_spawn_time[i])

            v = self.fire_p_vel[i]
            p = self.fire_p_pos[i]

            v /= 1. + (1. * GameState.delta_time)
            v += Vec3(0., 1.2, 0.) * GameState.delta_time
            p += v * GameState.delta_time

            if lf <= 0.:
                to_remove.append(i)

            else:
                point_data.extend(p)
                lifetime_data.append(lf)

                avg_pos += p

        for offset, i in enumerate(to_remove):
            self.fire_p_pos.pop(i - offset)
            self.fire_p_vel.pop(i - offset)
            self.fire_p_spawn_time.pop(i - offset)

        # send as a mesh to the gpu

        if lifetime_data:
            avg_pos /= len(lifetime_data)
        self.fire_point_trans.set_pos(avg_pos)

        vert_buf = np.array(point_data, dtype=np.float32)
        lifetime_buf = np.array(lifetime_data, dtype=np.float32)
        self.fire_point_mesh.write_to(vert_buf, vertex_count=len(lifetime_data), gl_usage=gl.GL_STREAM_DRAW)

        # hack a "out of format" lifetime buffer into the mesh vao
        gl.glBindVertexArray(self.fire_point_mesh.mesh_vao)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.fire_point_lifetime_buf)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, lifetime_buf, gl.GL_STREAM_DRAW)

        gl.glVertexAttribPointer(1, 1, gl.GL_FLOAT, False, 4, None)
        gl.glEnableVertexAttribArray(1)

        gl.glBindVertexArray(0)

        # refresh renderer with new data
        self.fire_point_renderer.refresh_show()
        seq.next(self._update_point_mesh)

    def _new_fire_particle(self, forward_dir: Vec3) -> None:
        # calc origin from view model space
        origin = Vec3(*(SpsState.p_hud_view_mesh.view_space_trans._trans_matrix @ np.array([0., -.8, .8, 1.], dtype=np.float32))[0:3])

        self.fire_p_pos.append(origin)
        self.fire_p_vel.append(forward_dir * 2. + Vec3(random.uniform(-.5, .5), random.uniform(-.5, .5), random.uniform(-.5, .5)) + SpsState.p_active_controller.p_vel)
        self.fire_p_spawn_time.append(GameState.current_time)

    @np.errstate(all='ignore')
    def tick(self):
        mb = pg.mouse.get_pressed()

        # process fire input

        if mb[0] and SpsState.p_ammo > 0:
            # modify inter-frame state

            push_mode = mb[0]
            self.view_knockback = Vec3(random.uniform(-.005, .005), random.uniform(-.005, .005), (.2 if push_mode else -.2) + random.uniform(-.01, .01))
            
            SpsState.p_ammo -= 1
            SpsState.p_ammo_regen_cooldown = GameState.current_time + 2.

            # hit scan and damage

            forward_dir = SpsState.p_active_controller.view_forward

            fire_pos = SpsState.p_active_controller.p_pos + SpsState.p_active_controller.CAMERA_OFFSET
            fire_pos += forward_dir * (min(abs((SpsState.p_active_controller.PLAYER_SIZE.x + .5) / np.float32(forward_dir.x)), abs((SpsState.p_active_controller.PLAYER_SIZE.y + .5) / np.float32(forward_dir.y)), abs((SpsState.p_active_controller.PLAYER_SIZE.z + .5) / np.float32(forward_dir.z)))) # converting to np.float32 to make div by zero a "valid" operation

            coll_test_ray = PhysRay.make(fire_pos, SpsState.p_active_controller.view_forward, Vec3(.1, .1, .1))
            fire_ray = PhysRay.make(fire_pos, SpsState.p_active_controller.view_forward, Vec3(1., 1., 1.))

            coll_hit = GameState.collider_scene.first_hit(coll_test_ray)
            box_hits = SpsState.hitbox_scene.all_hits(fire_ray, 2. if coll_hit is None else min(2., coll_hit.tmin))

            for hit in box_hits:
                hit_pos = Vec3(*hit.pos)
                hit.usr.on_damage(5, hit_pos)
                hit.usr.set_fire(8.)

            # spawn visual

            self._new_fire_particle(forward_dir)

        # reload ammo when valid

        if SpsState.p_ammo < 250 and GameState.current_time > SpsState.p_ammo_regen_cooldown:
            SpsState.p_ammo = min(250, SpsState.p_ammo + 2)
            SpsState.p_ammo_regen_cooldown = GameState.current_time

        # update view model

        self.view_knockback /= 1. + (20. * GameState.delta_time)
        SpsState.p_hud_view_mesh.view_space_trans.set_pos(self.view_initial_pos + self.view_knockback)

    view_initial_pos: Vec3
    view_knockback: Vec3

    fire_p_pos: list[Vec3]
    fire_p_vel: list[Vec3]
    fire_p_spawn_time: list[float]

    fire_point_mesh: GPUMesh
    fire_point_trans: Transform
    fire_point_lifetime_buf: np.uint32
    fire_point_renderer: ParticleRenderer

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

            push_mode = mb[0]
            self.view_knockback = Vec3(random.uniform(-.005, .005), random.uniform(-.005, .005), (.2 if push_mode else -.2) + random.uniform(-.01, .01))
            
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

            # apply force to hits
            for hit in box_hits:
                hit.usr.on_force(forward_dir * 50. if push_mode else (fire_pos - Vec3(*hit.pos)).normalize() * 35.)

            # apply reverse force to player
            SpsState.p_active_controller.p_vel += (-forward_dir * 1.5 if push_mode else forward_dir * 1.) * GameState.delta_time

        # reload ammo when valid

        if SpsState.p_ammo < 250 and GameState.current_time > SpsState.p_ammo_regen_cooldown:
            SpsState.p_ammo = min(250, SpsState.p_ammo + 5)
            SpsState.p_ammo_regen_cooldown = GameState.current_time + .05

        # update view model

        self.view_knockback /= 1. + (20. * GameState.delta_time)
        SpsState.p_hud_view_mesh.view_space_trans.set_pos(self.view_initial_pos + self.view_knockback)

    view_initial_pos: Vec3
    view_knockback: Vec3