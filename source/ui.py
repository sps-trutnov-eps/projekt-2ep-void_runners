import imgui
import math
from engine.cue.cue_state import GameState
from engine.cue.im2d import im2d_draw as im2d
from sps_state import SpsState
import time

class GameUI:
    def __init__(self):
        # Initialize animation variables
        self.pulse_animation = 0
        self.last_health = 100
        self.displayed_health = 100
        self.health_change_time = 0
        self.damage_flash = 0
        self.heart_texture = GameState.asset_manager.load_texture("textures/hpsrdce.png")

    def render_ui(self):
        self.ctx = im2d.Im2DContext(GameState.renderer.fullscreen_imgui_ctx)
        current_time = time.perf_counter()
        
        # Update animations
        self.pulse_animation = (math.sin(current_time * 2) + 1) * 0.5
        
        # Smooth health changes
        if self.last_health != SpsState.p_health:
            self.health_change_time = current_time
            self.damage_flash = 1.0
            self.last_health = SpsState.p_health
        
        # Interpolate displayed health
        health_transition = min(1.0, (current_time - self.health_change_time) * 3)
        self.displayed_health += (SpsState.p_health - self.displayed_health) * health_transition
        
        # Update damage flash
        self.damage_flash = max(0, self.damage_flash - GameState.delta_time * 2)
        
        # Main UI background with dynamic opacity
        background_alpha = 0.8 + self.pulse_animation * 0.1
        self.ctx.add_rect_filled(
            40, 530, 310, 690,
            imgui.get_color_u32_rgba(0, 0, 0, background_alpha)
        )
        
        # Health display with animations
        health_color = imgui.get_color_u32_rgba(
            1.0 if self.damage_flash > 0 else 0.2,
            1.0 if SpsState.p_health > 30 else 0.2,
            0.2,
            1.0
        )
        
        # Health bar
        health_width = 250 * (self.displayed_health / 100)
        self.ctx.add_rect_filled(
            60, 580, 60 + health_width, 595,
            health_color
        )
        self.ctx.add_rect(
            60, 580, 310, 595,
            imgui.get_color_u32_rgba(1, 1, 1, 0.5)
        )
        
        # Health icon with pulse effect when low
        icon_scale = 1.0 + (self.pulse_animation * 0.2 if SpsState.p_health < 30 else 0)
        icon_size = 64 * icon_scale
        self.ctx.add_image(
            self.heart_texture,
            (35, 510),
            (35 + icon_size, 510 + icon_size)
        )
        
        # Health text with shadow
        self.ctx.add_text(
            65, 551,
            imgui.get_color_u32_rgba(0, 0, 0, 1),
            f"Health: {int(self.displayed_health)}"
        )
        self.ctx.add_text(
            64, 550,
            health_color,
            f"Health: {int(self.displayed_health)}"
        )
        
        # Ammo display
        ammo_color = imgui.get_color_u32_rgba(1, 1, 1, 1)
        if SpsState.p_ammo < 5:
            ammo_color = imgui.get_color_u32_rgba(
                1.0,
                0.2 + self.pulse_animation * 0.8,
                0.2,
                1.0
            )
            
        self.ctx.add_text(
            65, 611,
            imgui.get_color_u32_rgba(0, 0, 0, 1),
            f"Ammo: {SpsState.p_ammo}"
        )
        self.ctx.add_text(
            64, 610,
            ammo_color,
            f"Ammo: {SpsState.p_ammo}"
        )
        
        # Score display
        self.ctx.add_text(
            65, 661,
            imgui.get_color_u32_rgba(0, 0, 0, 1),
            f"Score: {0}"  # Zde by mělo být napojení na skutečné skóre
        )
        self.ctx.add_text(
            64, 660,
            imgui.get_color_u32_rgba(1, 1, 1, 1),
            f"Score: {0}"
        )

        # Draw decorative elements
        self.ctx.add_line(
            60, 605,
            290, 605,
            imgui.get_color_u32_rgba(1, 1, 1, 0.3),
            1.0
        )
        self.ctx.add_line(
            60, 655,
            290, 655,
            imgui.get_color_u32_rgba(1, 1, 1, 0.3),
            1.0
        )