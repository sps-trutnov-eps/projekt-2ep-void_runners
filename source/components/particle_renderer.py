from engine.cue.rendering import cue_scene as sc
from engine.cue import cue_utils as utils

from engine.cue.rendering.cue_batch import DrawInstance, UniformBindTypes, UniformBind
from engine.cue.cue_state import GameState
from engine.cue.components.cue_transform import Transform
from engine.cue.rendering.cue_resources import GPUMesh

import numpy as np
import OpenGL.GL as gl 
from pygame.math import Vector3 as Vec3, Vector2 as Vec2

# a simple crude point mesh particle renderer helper

class ParticleRenderer:
    def __init__(self, en_data: dict, point_mesh: GPUMesh, en_trans: Transform | None, target_scene: 'sc.RenderScene | None' = None) -> None:
        # load assets from preload or disk
        
        self.mesh = point_mesh
        self.pipeline = GameState.asset_manager.load_shader(en_data["a_model_vshader"], en_data["a_model_fshader"])

        self.model_textures = tuple()
        if "a_model_albedo" in en_data:
            self.model_textures = (GameState.asset_manager.load_texture(en_data["a_model_albedo"]),)

        self.shader_uniform_data = []

        if "a_model_uniforms" in en_data:
            for n, v in en_data["a_model_uniforms"].items():
                loc = gl.glGetUniformLocation(self.pipeline.shader_program, n)

                if loc == -1:
                    utils.warn(f"[ModelRenderer] failed to get uniform \"{n}\"")

                if isinstance(v, float):
                    t = UniformBindTypes.FLOAT1
                    v = np.float32(v)
                elif isinstance(v, int):
                    t = UniformBindTypes.SINT1
                    v = np.int32(v)
                elif isinstance(v, Vec2):
                    t = UniformBindTypes.FLOAT2
                    v = np.array(v, dtype=np.float32)
                elif isinstance(v, Vec3):
                    t = UniformBindTypes.FLOAT3
                    v = np.array(v, dtype=np.float32)
                else:
                    utils.error(f"[ModelRenderer] value \"{v}\" cannot be used for a gl uniform")
                    continue

                self.shader_uniform_data.append(UniformBind(t, loc, v))

        self.model_opaque = True
        if en_data.get("a_model_transparent", False):
            self.model_opaque = False

        if target_scene is None:
            target_scene = GameState.active_scene

        self.scene = target_scene
        self.draw_ins = DrawInstance(self.mesh, self.pipeline, self.model_textures, self.model_opaque, self.shader_uniform_data, en_trans, ParticleRenderer._setup_particle_batch, ParticleRenderer._restore_gl_state, gl.GL_POINTS)
        self.model_transform = en_trans

        # insert model into the render_scene

        self.is_visible = False
        self.show()

    def __del__(self) -> None:
        self.despawn()

    @staticmethod
    def _setup_particle_batch() -> None:
        gl.glBlendFunc(gl.GL_ONE, gl.GL_ONE)
        gl.glDepthMask(gl.GL_FALSE)

    @staticmethod
    def _restore_gl_state() -> None:
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glDepthMask(gl.GL_TRUE)

    def refresh_show(self) -> None:
        self.hide()
        self.draw_ins = DrawInstance(self.mesh, self.pipeline, self.model_textures, self.model_opaque, self.shader_uniform_data, self.model_transform, ParticleRenderer._setup_particle_batch, ParticleRenderer._restore_gl_state, gl.GL_POINTS)
        self.show()

    def despawn(self) -> None:
        self.hide()
        self.draw_ins = None

    # start rendering this model if hidden
    def show(self) -> None:
        if self.draw_ins is None:
            return # despawned

        if not self.is_visible:
            self.scene.append(self.draw_ins)
            self.is_visible = True

    # stop rendering this model without deleting it (yet)
    def hide(self) -> None:
        if self.draw_ins is None:
            return # despawned

        if self.is_visible:
            self.scene.remove(self.draw_ins)
            self.is_visible = False
