from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from components.player_move import PlayerMovement
    from ui import GameUI

    from engine.cue.phys.cue_phys_scene import PhysScene

# a shared state for the entire game, mostly for player <-> enemy interaction code

class SpsState:
    # == player and hud state ==

    p_active_controller: 'PlayerMovement | None'

    p_health: int
    p_ammo: int

    p_hud_selected_weapon: int | None = None
    p_hud_ui: 'GameUI'

    dev_con: bool = False

    # == enemy states ==

    

    # == damage system ==

    hitbox_scene: 'PhysScene'