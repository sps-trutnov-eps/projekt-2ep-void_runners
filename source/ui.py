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
        
        # UI Layout constants
        self.PADDING = 15
        self.CORNER_RADIUS = 10
        self.UI_WIDTH = 280
        self.UI_HEIGHT = 180
        
        # Calculate position offsets (right bottom corner)
        self.offset_x = -self.UI_WIDTH - self.PADDING
        self.offset_y = -self.UI_HEIGHT - self.PADDING
        
        # Load textures
        self.heart_texture = GameState.asset_manager.load_texture("textures/hpsrdce.png")

    def render_rounded_panel(self, x, y, width, height, color):
        """Helper method to draw a rounded panel with border"""
        # Background
        self.ctx.add_rect_filled(
            x, y, x + width, y + height,
            color,
            rounding=self.CORNER_RADIUS
        )
        # Border
        self.ctx.add_rect(
            x, y, x + width, y + height,
            imgui.get_color_u32_rgba(1, 1, 1, 0.3),
            rounding=self.CORNER_RADIUS,
            thickness=1.0
        )

    def render_ui(self):
        self.ctx = im2d.Im2DContext(GameState.renderer.fullscreen_imgui_ctx)
        current_time = time.perf_counter()

        screen_width, screen_height = GameState.renderer.win_res
        base_x = screen_width + self.offset_x
        base_y = screen_height + self.offset_y
        
        # Update animations
        self.pulse_animation = (math.sin(current_time * 2) + 1) * 0.5
        
        # Smooth health changes
        if self.last_health != SpsState.p_health:
            self.health_change_time = current_time
            self.damage_flash = 1.0
            self.last_health = SpsState.p_health
        
        health_transition = min(1.0, (current_time - self.health_change_time) * 3)
        self.displayed_health += (SpsState.p_health - self.displayed_health) * health_transition
        self.damage_flash = max(0, self.damage_flash - GameState.delta_time * 2)

        # Main panel background
        self.render_rounded_panel(
            base_x, 
            base_y,
            self.UI_WIDTH,
            self.UI_HEIGHT,
            imgui.get_color_u32_rgba(0, 0, 0, 0.8 + self.pulse_animation * 0.1)
        )

        # Health Section
        health_color = imgui.get_color_u32_rgba(
            1.0 if self.damage_flash > 0 else 0.2,
            1.0 if SpsState.p_health > 30 else 0.2,
            0.2,
            1.0
        )

        # Health icon
        icon_scale = 1.0 + (self.pulse_animation * 0.2 if SpsState.p_health < 30 else 0)
        icon_size = 32 * icon_scale
        icon_x = base_x + self.PADDING
        icon_y = base_y + self.PADDING
        
        self.ctx.add_image(
            self.heart_texture,
            (icon_x, icon_y),
            (icon_x + icon_size, icon_y + icon_size)
        )

        # Health bar background
        health_bar_x = icon_x + icon_size + 10
        health_bar_y = icon_y + 8
        health_bar_width = 180
        health_bar_height = 16
        
        self.ctx.add_rect_filled(
            health_bar_x, 
            health_bar_y,
            health_bar_x + health_bar_width,
            health_bar_y + health_bar_height,
            imgui.get_color_u32_rgba(0.2, 0.2, 0.2, 0.8),
            rounding=4
        )

        # Health bar fill
        health_width = health_bar_width * (self.displayed_health / 100)
        self.ctx.add_rect_filled(
            health_bar_x,
            health_bar_y,
            health_bar_x + health_width,
            health_bar_y + health_bar_height,
            health_color,
            rounding=4
        )

        # Health text
        health_text = f"{int(self.displayed_health)}%"
        self.ctx.add_text(
            health_bar_x + health_bar_width/2 - 15,
            health_bar_y,
            imgui.get_color_u32_rgba(1, 1, 1, 1),
            health_text
        )

        # Ammo Section
        ammo_y = icon_y + icon_size + 20
        ammo_color = imgui.get_color_u32_rgba(1, 1, 1, 1)
        if SpsState.p_ammo < 5:
            ammo_color = imgui.get_color_u32_rgba(
                1.0,
                0.2 + self.pulse_animation * 0.8,
                0.2,
                1.0
            )

        # Ammo background
        self.render_rounded_panel(
            base_x + self.PADDING,
            ammo_y,
            120,
            40,
            imgui.get_color_u32_rgba(0.15, 0.15, 0.15, 0.9)
        )

        # Ammo text
        self.ctx.add_text(
            base_x + self.PADDING * 2,
            ammo_y + 12,
            ammo_color,
            f"Ammo: {SpsState.p_ammo}"
        )

        # Score Section
        score_y = ammo_y + 50
        
        # Score background
        self.render_rounded_panel(
            base_x + self.PADDING,
            score_y,
            120,
            40,
            imgui.get_color_u32_rgba(0.15, 0.15, 0.15, 0.9)
        )

        # Score text
        score = 0  # Replace with actual score
        self.ctx.add_text(
            base_x + self.PADDING * 2,
            score_y + 12,
            imgui.get_color_u32_rgba(1, 1, 1, 1),
            f"Score: {score}"
        )

        # Optional: Add visual feedback for important events
        if self.damage_flash > 0:
            flash_alpha = self.damage_flash * 0.3
            self.ctx.add_rect_filled(
                base_x,
                base_y,
                base_x + self.UI_WIDTH,
                base_y + self.UI_HEIGHT,
                imgui.get_color_u32_rgba(1, 0, 0, flash_alpha),
                rounding=self.CORNER_RADIUS
            )