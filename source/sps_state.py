from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from components.player_move import PlayerMovement
    from ui import GameUI
    from mainmenu import MenuUI

    from engine.cue.phys.cue_phys_scene import PhysScene, PhysAABB

# a shared state for the entire game, mostly for player <-> enemy interaction code

class SpsState:
    # == player and hud state ==
    # this should be a player class / entity but too late..

    p_active_controller: 'PlayerMovement'
    p_hitbox: 'PhysAABB'

    p_health: int
    p_ammo: int

    p_hud_selected_weapon: int | None = None
    p_hud_ui: 'GameUI | MenuUI | None'

    p_death_timestamp: float

    # == enemy states ==

    

    # == damage system ==

    hitbox_scene: 'PhysScene'

    # == dev bools ==

    is_perf_overlay_open: bool = True
    is_dev_con_open: bool = False
    dev_vis_sub_zones: bool = True
    dev_vis_sub_zone_target: None | str = None

    cheat_deltascale: float = 1.

    cheat_ai_debug: bool = True
    cheat_nodmg: bool = False