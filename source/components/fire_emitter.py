from dataclasses import dataclass
import random

from engine.cue.cue_state import GameState
from engine.cue import cue_sequence as seq
from engine.cue.rendering.cue_resources import GPUMesh
from engine.cue.components.cue_transform import Transform

from components.particle_renderer import ParticleRenderer
from sps_state import SpsState

from pygame.math import Vector3 as Vec3
import numpy as np
from OpenGL import GL as gl

@dataclass(init=False, slots=True)
class FireEmitter:
    def __init__(self) -> None:
        self.fire_p_pos = []
        self.fire_p_vel = []
        self.fire_p_spawn_time = []

        self.fire_emit_origin = Vec3()
        self.fire_emit_cooldown = 0
        self.emitter_on_fire = False

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

        seq.next(self._tick)

    def _tick(self) -> None:
        # spawn new particles if on fire

        if self.emitter_on_fire and GameState.current_time - self.fire_emit_cooldown > .02:
            self.fire_emit_cooldown = GameState.current_time
            self._new_fire_particle(Vec3())

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
        seq.next(self._tick)

    def _new_fire_particle(self, forward_dir: Vec3) -> None:
        self.fire_p_pos.append(Vec3(self.fire_emit_origin))
        self.fire_p_vel.append(forward_dir * 2. + Vec3(random.uniform(-.5, .5), random.uniform(-.5, .5), random.uniform(-.5, .5)))
        self.fire_p_spawn_time.append(GameState.current_time)

    def set_on_fire(self, is_on_fire: bool) -> None:
        self.emitter_on_fire = is_on_fire

    def set_origin(self, origin: Vec3) -> None:
        self.fire_emit_origin = origin

    fire_p_pos: list[Vec3]
    fire_p_vel: list[Vec3]
    fire_p_spawn_time: list[float]

    fire_emit_origin: Vec3
    fire_emit_cooldown: float
    emitter_on_fire: bool

    fire_point_mesh: GPUMesh
    fire_point_trans: Transform
    fire_point_lifetime_buf: np.uint32
    fire_point_renderer: ParticleRenderer