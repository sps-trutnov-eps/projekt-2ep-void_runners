from engine.cue.cue_state import GameState
from engine.cue.im2d import im2d_draw as im2d
import imgui
import math
import time
import sys
import pygame as pg
from engine.cue import cue_map
from sps_state import SpsState
from ui import GameUI

from engine.cue.cue_state import GameState
from engine.cue.im2d import im2d_draw as im2d
import imgui
import math
import time
import sys
import pygame as pg
from engine.cue import cue_map
from sps_state import SpsState
from ui import GameUI

class CharacterSelectUI:
    def __init__(self, on_back):
        self.start_time = time.time()
        self.animation_progress = 0.0
        self.on_back = on_back
        self.mouse_pressed = False
        
        # Načtení základní textury pro ikony
        self.default_icon = GameState.asset_manager.load_texture("textures/annonym.png")
        
        self.characters = [
            {
                "name": "Heavy",
                "description": "Tank with high HP",
                "icon": self.default_icon,
                
            },
            {
                "name": "Commando",
                "description": "Well equipped soldier",
                "icon": self.default_icon,
                
            },
            {
                "name": "Assassin",
                "description": "Fast and agile fighter with double jump",
                "icon": self.default_icon,
                
            }
        ]
        self.selected_character = None
        
        self.colors = {
            "primary": (0.2, 0.6, 1.0, 1.0),
            "secondary": (0.1, 0.3, 0.8, 1.0),
            "accent": (1.0, 0.5, 0.0, 1.0),
            "text": (1.0, 1.0, 1.0, 1.0),
            "background": (0.05, 0.05, 0.1, 0.9)
        }

    def render_ui(self):
        self.ctx = im2d.Im2DContext(GameState.renderer.fullscreen_imgui_ctx)
        current_time = time.time()
        self.animation_progress = min(1.0, (current_time - self.start_time) * 2)
        
        screen_width, screen_height = 1280, 720
        
        # Pozadí
        self.ctx.add_rect_filled_multicolor(
            0, 0, screen_width, screen_height,
            imgui.get_color_u32_rgba(0.05, 0.05, 0.1, 0.95),
            imgui.get_color_u32_rgba(0.1, 0.1, 0.2, 0.95),
            imgui.get_color_u32_rgba(0.05, 0.05, 0.1, 0.95),
            imgui.get_color_u32_rgba(0.02, 0.02, 0.05, 0.95)
        )
        
        # Nadpis
        title = "SELECT YOUR CHARACTER"
        title_width = imgui.calc_text_size(title).x
        self.ctx.add_text(
            (screen_width - title_width) / 2, 50,
            imgui.get_color_u32_rgba(1, 1, 1, 1),
            title
        )
        
        # Vykreslení karet postav
        card_width = 300
        card_height = 400
        spacing = 50
        start_x = (screen_width - (card_width * 3 + spacing * 2)) / 2
        
        mouse_pos = imgui.get_mouse_pos()
        mouse_clicked = pg.mouse.get_pressed()[0]
        
        # Detekce kliknutí
        if mouse_clicked and not self.mouse_pressed:
            self.mouse_pressed = True
        elif not mouse_clicked and self.mouse_pressed:
            self.mouse_pressed = False
            # Kontrola kliknutí na tlačítko zpět
            if 20 <= mouse_pos.x <= 120 and 20 <= mouse_pos.y <= 60:
                self.on_back()
        
        # Tlačítko zpět
        back_hovered = 20 <= mouse_pos.x <= 120 and 20 <= mouse_pos.y <= 60
        back_color = self.colors["accent"] if back_hovered else self.colors["primary"]
        self.ctx.add_rect_filled(20, 20, 120, 60, imgui.get_color_u32_rgba(*back_color))
        self.ctx.add_text(45, 30, imgui.get_color_u32_rgba(1, 1, 1, 1), "Back")
        
        # Vykreslení postav
        for i, char in enumerate(self.characters):
            x = start_x + i * (card_width + spacing)
            y = 150
            
            # Detekce hoveru
            is_hovered = (x <= mouse_pos.x <= x + card_width and
                         y <= mouse_pos.y <= y + card_height)
            
            # Kliknutí na kartu
            if self.mouse_pressed and is_hovered:
                self.selected_character = i
            
            # Efekt vybrané/hoverované karty
            if is_hovered or self.selected_character == i:
                card_color = self.colors["accent"]
                y -= 10  # Mírně zvednout kartu
            else:
                card_color = self.colors["primary"]
            
            # Karta postavy
            self.ctx.add_rect_filled(x, y, x + card_width, y + card_height,
                                   imgui.get_color_u32_rgba(*card_color))
            
            # Ikona postavy
            icon_size = 200
            self.ctx.add_image(char["icon"],
                             (x + (card_width - icon_size) / 2, y + 30),
                             (x + (card_width + icon_size) / 2, y + 30 + icon_size))
            
            # Jméno postavy
            name_width = imgui.calc_text_size(char["name"]).x
            self.ctx.add_text(x + (card_width - name_width) / 2, y + icon_size + 50,
                            imgui.get_color_u32_rgba(1, 1, 1, 1), char["name"])
            
            # Popis postavy
            desc_width = imgui.calc_text_size(char["description"]).x
            self.ctx.add_text(x + (card_width - desc_width) / 2, y + icon_size + 80,
                            imgui.get_color_u32_rgba(0.8, 0.8, 0.8, 1), char["description"])
            
            # Tlačítko Select
            button_width = 120
            button_x = x + (card_width - button_width) / 2
            button_y = y + card_height - 50
            
            button_hovered = (button_x <= mouse_pos.x <= button_x + button_width and
                            button_y <= mouse_pos.y <= button_y + 30)
            
            button_color = self.colors["accent"] if button_hovered else self.colors["secondary"]
            self.ctx.add_rect_filled(button_x, button_y, button_x + button_width, button_y + 30,
                                   imgui.get_color_u32_rgba(*button_color))
            
            select_text = "Selected" if self.selected_character == i else "Select"
            text_width = imgui.calc_text_size(select_text).x
            self.ctx.add_text(button_x + (button_width - text_width) / 2, button_y + 5,
                            imgui.get_color_u32_rgba(1, 1, 1, 1), select_text)

class MenuUI:
    def __init__(self):
        self.background_tex = GameState.asset_manager.load_texture("textures/def_white.png")
        self.logo_tex = GameState.asset_manager.load_texture("textures/name.png")
        self.start_time = time.time()
        self.buttons = [
            {"text": "PLAY", "action": self.start_game},
            {"text": "LOADOUT", "action": self.show_loadout},
            {"text": "OPTIONS", "action": self.show_options},
            {"text": "EXIT", "action": self.exit_game}
        ]
        self.selected_button = None
        self.animation_progress = 0.0
        self.mouse_pressed = False
        self.first_map = "assets/maps/camp/c0_wakeup_p2.json"
        self.current_screen = "main"  # main nebo loadout
        self.loadout_screen = CharacterSelectUI(self.back_to_main)
        
        self.colors = {
            "primary": (0.2, 0.6, 1.0, 1.0),
            "secondary": (0.1, 0.3, 0.8, 1.0),
            "accent": (1.0, 0.5, 0.0, 1.0),
            "text": (1.0, 1.0, 1.0, 1.0),
            "background": (0.05, 0.05, 0.1, 0.9)
        }

    def animate_value(self, start, end, progress):
        return start + (end - start) * (1 - math.cos(progress * math.pi)) / 2

    def back_to_main(self):
        self.current_screen = "main"

    def show_loadout(self):
        self.current_screen = "loadout"
        self.loadout_screen = CharacterSelectUI(self.back_to_main)

    def render_ui(self):
        if self.current_screen == "main":
            self.render_main_menu()
        elif self.current_screen == "loadout":
            self.loadout_screen.render_ui()

    def render_main_menu(self):
        self.ctx = im2d.Im2DContext(GameState.renderer.fullscreen_imgui_ctx)
        current_time = time.time()
        
        # Aktualizace animace
        self.animation_progress = min(1.0, (current_time - self.start_time) * 2)
        
        # === Pozadí ===
        screen_width, screen_height = 1280, 720
        
        # Vykreslení tmavého pozadí s gradientem
        self.ctx.add_rect_filled_multicolor(
            0, 0, screen_width, screen_height,
            imgui.get_color_u32_rgba(0.05, 0.05, 0.1, 0.95),
            imgui.get_color_u32_rgba(0.1, 0.1, 0.2, 0.95),
            imgui.get_color_u32_rgba(0.05, 0.05, 0.1, 0.95),
            imgui.get_color_u32_rgba(0.02, 0.02, 0.05, 0.95)
        )
        
        # === Logo ===
        logo_size = 200
        logo_y = self.animate_value(-logo_size, 100, self.animation_progress)
        self.ctx.add_image(
            self.logo_tex,
            ((screen_width - logo_size) / 2, logo_y),
            ((screen_width + logo_size) / 2, logo_y + logo_size)
        )
        
        # === Menu tlačítka ===
        button_width = 300
        button_height = 60
        button_spacing = 20
        start_y = 300
        
        # Získání stavu myši
        mouse_pos = imgui.get_mouse_pos()
        mouse_clicked = pg.mouse.get_pressed()[0]
        
        # Detekce kliknutí
        if mouse_clicked and not self.mouse_pressed:
            self.mouse_pressed = True
        elif not mouse_clicked and self.mouse_pressed:
            self.mouse_pressed = False
            # Kontrola kliknutí na tlačítko
            for i, button in enumerate(self.buttons):
                button_x = (screen_width - button_width) / 2
                button_y = start_y + i * (button_height + button_spacing)
                
                if (button_x <= mouse_pos.x <= button_x + button_width and
                    button_y <= mouse_pos.y <= button_y + button_height):
                    button["action"]()
        
        for i, button in enumerate(self.buttons):
            # Animace postupného objevení tlačítek
            button_alpha = max(0.0, min(1.0, (self.animation_progress - i * 0.2) * 2))
            
            # Výpočet pozice tlačítka
            button_x = (screen_width - button_width) / 2
            button_y = start_y + i * (button_height + button_spacing)
            
            # Detekce hoveru
            is_hovered = (
                button_x <= mouse_pos.x <= button_x + button_width and
                button_y <= mouse_pos.y <= button_y + button_height
            )
            
            # Efekt hoveru
            if is_hovered:
                pulse = (math.sin(current_time * 5) + 1) * 0.5 * 0.2
                hover_width = button_width + 20
                hover_x = button_x - 10
            else:
                pulse = 0
                hover_width = button_width
                hover_x = button_x
            
            # Pozadí tlačítka
            button_color = self.colors["primary"] if not is_hovered else self.colors["accent"]
            button_color = (*button_color[:3], button_color[3] * button_alpha)
            
            # Hlavní tělo tlačítka
            self.ctx.add_rect_filled(
                hover_x, button_y,
                hover_x + hover_width, button_y + button_height,
                imgui.get_color_u32_rgba(*button_color)
            )
            
            # Okraj tlačítka
            border_color = (*self.colors["secondary"][:3], self.colors["secondary"][3] * button_alpha)
            self.ctx.add_rect(
                hover_x, button_y,
                hover_x + hover_width, button_y + button_height,
                imgui.get_color_u32_rgba(*border_color),
                thickness=2
            )
            
            # Text tlačítka
            text_width = imgui.calc_text_size(button["text"]).x
            text_x = button_x + (button_width - text_width) / 2
            text_y = button_y + (button_height - 20) / 2
            
            text_color = (*self.colors["text"][:3], self.colors["text"][3] * button_alpha)
            self.ctx.add_text(
                text_x, text_y,
                imgui.get_color_u32_rgba(*text_color),
                button["text"]
            )
            
            # Dekorativní prvky při hoveru
            if is_hovered:
                # Svítící okraj
                glow_color = (*self.colors["accent"][:3], 0.3 * button_alpha)
                self.ctx.add_rect(
                    hover_x - 5, button_y - 5,
                    hover_x + hover_width + 5, button_y + button_height + 5,
                    imgui.get_color_u32_rgba(*glow_color),
                    thickness=2
                )
                
                # Animované rohy
                corner_size = 10 + pulse * 50
                corner_color = (*self.colors["accent"][:3], (0.5 + pulse) * button_alpha)
                
                # Levý horní roh
                self.ctx.add_line(
                    hover_x, button_y + corner_size,
                    hover_x, button_y,
                    imgui.get_color_u32_rgba(*corner_color),
                    2
                )
                self.ctx.add_line(
                    hover_x, button_y,
                    hover_x + corner_size, button_y,
                    imgui.get_color_u32_rgba(*corner_color),
                    2
                )
                
                # Pravý dolní roh
                self.ctx.add_line(
                    hover_x + hover_width - corner_size, button_y + button_height,
                    hover_x + hover_width, button_y + button_height,
                    imgui.get_color_u32_rgba(*corner_color),
                    2
                )
                self.ctx.add_line(
                    hover_x + hover_width, button_y + button_height - corner_size,
                    hover_x + hover_width, button_y + button_height,
                    imgui.get_color_u32_rgba(*corner_color),
                    2
                )

    def start_game(self):
        if hasattr(self.loadout_screen, 'selected_character') and self.loadout_screen.selected_character is not None:
            char = self.loadout_screen.characters[self.loadout_screen.selected_character]
            print(f"Starting game with {char['name']}")
            
            SpsState.p_hud_ui = GameUI()
            SpsState.dev_con = False
            
            cue_map.load_map(self.first_map)
        else:
            print("Please select a character first in the Loadout menu!")

    def show_options(self):
        print("Opening options...")

    def exit_game(self):
        print("Exiting game...")
        sys.exit(0)
                        