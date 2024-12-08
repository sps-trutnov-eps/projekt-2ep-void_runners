from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from components.player_move import PlayerMovement
    from sps_weapons import FdevImpl, GlockImpl, FlameImpl
    from ui import GameUI
    from mainmenu import MenuUI

    from engine.cue.phys.cue_phys_scene import PhysScene, PhysAABB
    from sps_post_pass import BloomPostPass, TonemapPostPass
    from entity.sps_nav_node import SpsNavNode
    from entity.sps_view_mesh import SpsViewMesh

# a shared state for the entire game, mostly for player <-> enemy interaction code

class SpsState:
    # == player and hud state ==
    # this should be a player class / entity but too late..

    p_active_controller: 'PlayerMovement'
    p_weapon_impl: 'FdevImpl | GlockImpl | FlameImpl'
    p_hitbox: 'PhysAABB'

    p_health: int
    
    p_ammo: int
    p_ammo_regen_cooldown: float

    p_selected_char: str
    p_hud_view_mesh: 'SpsViewMesh'
    p_hud_ui: 'GameUI | MenuUI | None'

    p_death_timestamp: float
    
    tonemap_post_pass: 'TonemapPostPass'

    # == enemy and damage system ==

    active_nav_nodes: list['SpsNavNode']
    hitbox_scene: 'PhysScene'

    active_drone_count: int

    # == dev bools ==

    is_perf_overlay_open: bool = False
    is_post_config_open: bool = False
    is_dev_con_open: bool = False
    dev_vis_sub_zones: bool = False
    dev_vis_sub_zone_target: None | str = None

    cheat_deltascale: float = 1.

    cheat_ai_debug: bool = False
    cheat_nodmg: bool = False
    cheat_ai_invis: bool = False