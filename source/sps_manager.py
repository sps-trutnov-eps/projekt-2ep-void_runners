from engine.cue.cue_state import GameState
from engine.cue import cue_sequence as seq
from engine.cue import cue_map

from sps_state import SpsState
from pygame.math import Vector3 as Vec3
import pygame as pg

# == global callbacks for managing the game (and player) as a whole ==

def p_respawn_cb(e) -> None:
    # any key, don't care

    cue_map.load_map(GameState.current_map) # reload

def p_death() -> None:
    SpsState.p_health = 0

    SpsState.p_active_controller.movement_disabled = True
    SpsState.p_active_controller.view_overlay_pos = Vec3(0., -SpsState.p_active_controller.PLAYER_SIZE.y * .8, 0.)

    # FIXME: delete p_view_mesh
    # FIXME: delete player hitbox

    seq.on_event(pg.KEYDOWN, p_respawn_cb)

def p_take_damage(damage_value: int): #, damage_dir: Vec3) -> None:
    SpsState.p_health -= damage_value

    if SpsState.p_health <= 0:
        p_death()
        return

    # TODO: damage indicator view overlay