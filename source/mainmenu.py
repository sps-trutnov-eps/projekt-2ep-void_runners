from engine.cue.cue_state import GameState
from engine.cue.im2d import im2d_draw as im2d
import imgui

class MenuUI:
    def __init__(self):
        # Načtení textury pro pozadí
        self.tex = GameState.asset_manager.load_texture("textures/def_white.png")
        # Přidání stavu pro hover efekt
        self.is_play_hovered = False
        
    def render_ui(self):
        # Vytvoření 2D kontextu pro vykreslování
        self.ctx = im2d.Im2DContext(GameState.renderer.fullscreen_imgui_ctx)
        
        # Základní pozice a velikosti
        button_x, button_y = 20, 540
        button_width, button_height = 280, 140
        
        # Detekce myši pro hover efekt
        mouse_pos = imgui.get_mouse_pos()
        self.is_play_hovered = (
            button_x <= mouse_pos.x <= button_x + button_width and
            button_y <= mouse_pos.y <= button_y + button_height
        )
        
        # Barva tlačítka - červená, světlejší při hoveru
        button_color = imgui.get_color_u32_rgba(1, 0.2, 0.2, 1) if self.is_play_hovered else imgui.get_color_u32_rgba(0.8, 0, 0, 1)
        
        # Vykreslení tlačítka
        self.ctx.add_rect_filled(
            button_x, button_y,
            button_x + button_width, button_y + button_height,
            button_color
        )
        
        # Vykreslení textu "Play"
        text_color = imgui.get_color_u32_rgba(1, 1, 1, 1)
        self.ctx.add_text(50, 550, text_color, "Play")
        
        # Vykreslení textury (např. jako pozadí nebo ikona)
        self.ctx.add_image(
            self.tex,
            (40, 700),  # horní levý roh
            (240, 620)  # spodní pravý roh
        )