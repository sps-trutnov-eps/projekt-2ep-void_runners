from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from components.player_move import PlayerMovement
    from ui import GameUI
    from mainmenu import MenuUI

    from engine.cue.phys.cue_phys_scene import PhysScene

# a shared state for the entire game, mostly for player <-> enemy interaction code

class SpsState:
    # == player and hud state ==

    p_active_controller: 'PlayerMovement'

    p_health: int
    p_ammo: int

    p_hud_selected_weapon: int | None = None
    p_hud_ui: 'GameUI | MenuUI | None'

    dev_con: bool = False

    # == enemy states ==

    

    # == damage system ==

    hitbox_scene: 'PhysScene'

    # == dev bools ==

    ai_debug: bool = False