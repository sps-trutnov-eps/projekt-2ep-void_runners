import OpenGL.GL as gl
import numpy as np

from engine.cue.cue_state import GameState
from engine.cue import cue_utils as utils

from engine.cue.rendering.cue_framebuffer import RenderAttachment, RenderFramebuffer
from engine.cue.rendering.cue_resources import ShaderPipeline
from engine.cue.rendering.cue_post_pass import PostPass, SinglePassPostPass

# a not-so-optimized bloom pass implementation, implements the original siggraph 2014 CoD PBR bloom

class BloomPostPass(PostPass):
    BLOOM_LEVEL_COUNT = 8

    def __init__(self, initial_size: tuple[int, int]) -> None:
        super().__init__()

        self.downsample_pipeline = GameState.asset_manager.load_shader("shaders/post/fs_trig.vert", "shaders/post/bloom_down.frag")
        self.upsample_pipeline = GameState.asset_manager.load_shader("shaders/post/fs_trig.vert", "shaders/post/bloom_up.frag")

        self.downsample_res_loc = gl.glGetUniformLocation(self.downsample_pipeline.shader_program, "in_res")
        if self.downsample_res_loc == -1:
            utils.error("[BloomPostPass] failed to get uniform loc for in_res")

        self.level_fbs = []
        self.level_sizes = []

        self.resize(initial_size)

    def dispatch(self, src: RenderFramebuffer, dst_fb: np.uint32) -> None:
        # downsampling pass

        self.downsample_pipeline.bind()
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glDisable(gl.GL_BLEND)

        level_sizes = self.level_sizes
        level_fbs = self.level_fbs

        down_res_loc = self.downsample_res_loc

        # bind initial src in_res and in_tex 
        gl.glUniform2ui(down_res_loc, *self.src_size)
        gl.glBindTexture(gl.GL_TEXTURE_2D, src.fb_attachments[gl.GL_COLOR_ATTACHMENT0].texture_handle)

        for level_index in range(self.BLOOM_LEVEL_COUNT):
            level_size = level_sizes[level_index]

            # bind level fb
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, level_fbs[level_index].fb_handle)
            gl.glViewport(0, 0, *level_size)
            
            # dispatch a fullscreen trig
            gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)

            # bind in_res and in_tex for next level
            gl.glUniform2ui(down_res_loc, *level_size)
            gl.glBindTexture(gl.GL_TEXTURE_2D, level_fbs[level_index].fb_attachments[gl.GL_COLOR_ATTACHMENT0].texture_handle)

        # upsampling pass

        self.upsample_pipeline.bind()

        # upsample and blend into dst directly
        gl.glBindFramebuffer(gl.GL_READ_FRAMEBUFFER, src.fb_handle)
        gl.glBindFramebuffer(gl.GL_DRAW_FRAMEBUFFER, dst_fb)
        gl.glViewport(0, 0, *self.src_size)

        # altho a little unoptimized, blit the src fb into dst as the base, bloom will be blended on top
        gl.glBlitFramebuffer(0, 0, *self.src_size, 0, 0, *self.src_size, gl.GL_COLOR_BUFFER_BIT, gl.GL_NEAREST)

        # upscale bloom pass into the second attachment ready to be used by the tonemapper pass
        gl.glDrawBuffer(gl.GL_COLOR_ATTACHMENT1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_ONE, gl.GL_ONE)
        gl.glBlendEquation(gl.GL_FUNC_ADD)

        for level_index in range(self.BLOOM_LEVEL_COUNT - 1, 0, -1):
            # bind level to upsample
            gl.glBindTexture(gl.GL_TEXTURE_2D, level_fbs[level_index].fb_attachments[gl.GL_COLOR_ATTACHMENT0].texture_handle)

            # dispatch a fullscreen trig
            gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)

        # cleanup gl state

        gl.glDisable(gl.GL_BLEND)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        gl.glDrawBuffer(gl.GL_COLOR_ATTACHMENT0)
        gl.glUseProgram(0)

    def resize(self, size: tuple[int, int]) -> None:
        # recalc level sizes

        self.src_size = size
        
        self.level_sizes.clear()
        for i in range(1, self.BLOOM_LEVEL_COUNT + 1):
            self.level_sizes.append((size[0] // (2 ** i), size[1] // (2 ** i)))

        # resize level fbs

        level_attachments = [
            RenderAttachment(gl.GL_COLOR_ATTACHMENT0, gl.GL_FLOAT, gl.GL_RGB, gl.GL_R11F_G11F_B10F),
        ]
        
        self.level_fbs.clear()
        for i in range(self.BLOOM_LEVEL_COUNT):
            self.level_fbs.append(RenderFramebuffer(self.level_sizes[i], level_attachments))

    downsample_pipeline: ShaderPipeline
    upsample_pipeline: ShaderPipeline

    downsample_res_loc: np.uint32
    upsample_intensity_loc: np.uint32

    level_fbs: list[RenderFramebuffer]
    level_sizes: list[tuple[int, int]]
    src_size: tuple[int, int]

# a final tonemapping and gamma correction pass, should always be present for HDR rendering

class TonemapPostPass(SinglePassPostPass):
    def __init__(self) -> None:
        pipeline = GameState.asset_manager.load_shader("shaders/post/fs_trig.vert", "shaders/post/final_tonemap.frag")
        pipeline.bind()

        bloom_tex_loc = gl.glGetUniformLocation(pipeline.shader_program, "hdr_bloom")
        gl.glUniform1i(bloom_tex_loc, 1)

        self.bloom_enabled_loc = gl.glGetUniformLocation(pipeline.shader_program, "bloom_enabled")
        self.bloom_strength_loc = gl.glGetUniformLocation(pipeline.shader_program, "bloom_strength")

        self.exposure_loc = gl.glGetUniformLocation(pipeline.shader_program, "exposure")
        
        self.bloom_enabled = True
        self.bloom_strength = .04
        self.exposure = 1.

        super().__init__(pipeline)

    def setup_dispatch(self, src: RenderFramebuffer, dst_fb: np.uint32) -> None:
        # bind the bloom pass buffer
        src.fb_attachments[gl.GL_COLOR_ATTACHMENT1].bind_to(1)

        gl.glUniform1i(self.bloom_enabled_loc, int(self.bloom_enabled))
        gl.glUniform1f(self.bloom_strength_loc, self.bloom_strength)

        gl.glUniform1f(self.exposure_loc, self.exposure)