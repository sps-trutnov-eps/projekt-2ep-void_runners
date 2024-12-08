from engine.cue.rendering import cue_scene as sc
from engine.cue import cue_utils as utils, cue_sequence as seq

from engine.cue.rendering.cue_batch import DrawInstance, UniformBindTypes, UniformBind
from engine.cue.cue_state import GameState
from engine.cue.components.cue_transform import Transform
from engine.cue.rendering.cue_resources import GPUMesh

import numpy as np
import OpenGL.GL as gl 
from pygame.math import Vector3 as Vec3, Vector2 as Vec2

# a simple billboard line renderer component, based of the ModelRenderer

class LineRenderer:
    def __init__(self, en_data: dict, line_mesh: GPUMesh, initial_line_width: float, en_trans: Transform, target_scene: 'sc.RenderScene | None' = None) -> None:
        # load assets from preload or disk
        
        self.mesh = line_mesh
        self.pipeline = GameState.asset_manager.load_shader(en_data["a_model_vshader"], en_data["a_model_fshader"])

        self.model_textures = tuple()
        if "a_model_albedo" in en_data:
            self.model_textures = (GameState.asset_manager.load_texture(en_data["a_model_albedo"]),)

        self.shader_uniform_data = []
        self.line_width = initial_line_width

        # add line uniforms
        self.shader_uniform_data.append(UniformBind(UniformBindTypes.FLOAT3, gl.glGetUniformLocation(self.pipeline.shader_program, "cam_pos"), np.array([0., 0., 0.], dtype=np.float32)))
        self.shader_uniform_data.append(UniformBind(UniformBindTypes.FLOAT1, gl.glGetUniformLocation(self.pipeline.shader_program, "line_width"), np.float32(initial_line_width)))

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
        self.draw_ins = DrawInstance(self.mesh, self.pipeline, self.model_textures, self.model_opaque, self.shader_uniform_data, en_trans, LineRenderer._setup_batch, LineRenderer._restore_gl_state, )
        self.model_transform = en_trans

        # insert model into the render_scene

        self.is_visible = False
        self.show()

        seq.next(self._tick)

    def __del__(self) -> None:
        self.despawn()

    @staticmethod
    def _setup_batch() -> None:
        gl.glBlendFunc(gl.GL_ONE, gl.GL_ONE)

    @staticmethod
    def _restore_gl_state() -> None:
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def _tick(self) -> None:
        if self.draw_ins is None:
            return # despawned

        self.draw_ins.uniform_data[0].bind_value = np.array(GameState.active_camera.cam_pos, dtype=np.float32)
        self.draw_ins.uniform_data[1].bind_value = np.float32(self.line_width)

        seq.next(self._tick)

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
