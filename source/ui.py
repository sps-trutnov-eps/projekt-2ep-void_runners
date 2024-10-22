import imgui
from engine.cue.cue_state import GameState
from engine.cue.im2d import im2d_draw as im2d


class GameUI:
    def __init__(self, lives, ammo, score):
        self.lives = lives
        self.ammo = ammo
        self.score = score


    def render_ui(self):
        self.ctx = im2d.Im2DContext(GameState.renderer.fullscreen_imgui_ctx)
        self.ctx.add_rect_filled(50,540, 300,680, imgui.get_color_u32_rgba(0,0,0,1))

        self.tex = GameState.asset_manager.load_texture ("textures/hpsrdce.png")  
       
        self.ctx.add_text(50,550, imgui.get_color_u32_rgba(1,1,1,1), f"Lives: {self.lives}")
        self.ctx.add_image(self.tex, (40,530), (240,620))

        self.ctx.add_text(50,600, imgui.get_color_u32_rgba(1,1,1,1), f"Ammo: {self.ammo}")
        #self.ctx.add_text(imgui.get_color_u32_rgba(1,1,1,1))

        self.ctx.add_text(50,650, imgui.get_color_u32_rgba(1,1,1,1), f"Score: {self.score}")
        #self.ctx.add_text(imgui.get_color_u32_rgba(1,1,1,1))





