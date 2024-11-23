import imgui
from engine.cue.cue_state import GameState
from engine.cue.im2d import im2d_draw as im2d


class MenuUI:
    def __init__(self,):
        self.tex = GameState.asset_manager.load_texture("textures/def_white.png")


    def render_ui(self):
        self.ctx = im2d.Im2DContext(GameState.renderer.fullscreen_imgui_ctx)
        self.ctx.add_rect_filled(20,540, 300,680, imgui.get_color_u32_rgba(1,0,0,1))
        
        self.ctx.add_text(50,550, imgui.get_color_u32_rgba(1,1,1,1), f"Play")
        self.ctx.add_image(self.tex, (40,700), (240,620))                                                                                                                                           
