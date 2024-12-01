import os

from engine.cue.cue_state import GameState
from engine.cue import cue_sequence as seq
from engine.cue import cue_map
from engine.cue.phys.cue_phys_types import PhysAABB

from ui import GameUI
from sps_state import SpsState
from mainmenu import MenuUI

from pygame.math import Vector3 as Vec3
import pygame as pg

# == global callbacks for managing the game (and player) as a whole ==

def p_respawn_cb(e) -> None:
    # any key, don't care

    if GameState.current_time - SpsState.p_death_timestamp > 1.2: # long enough that people don't get confused, but short enough to not get anoying (hopefully)
        cue_map.load_map(GameState.current_map) # reload
    
    else:
        seq.on_event(pg.KEYDOWN, p_respawn_cb) # too early, wait for another key later

def p_death() -> None:
    SpsState.p_health = 0

    SpsState.p_active_controller.movement_disabled = True
    SpsState.p_active_controller.view_overlay_pos = Vec3(0., -SpsState.p_active_controller.PLAYER_SIZE.y * .8, 0.)

    SpsState.p_death_timestamp = GameState.current_time

    # FIXME: delete p_view_mesh
    
    SpsState.hitbox_scene.remove_coll(SpsState.p_hitbox)

    seq.on_event(pg.KEYDOWN, p_respawn_cb)

def p_take_damage(damage_value: int): #, damage_dir: Vec3) -> None:
    if SpsState.p_health == 0:
        return # already dead

    SpsState.p_health -= damage_value

    if SpsState.p_health <= 0:
        p_death()
        return

    # TODO: damage indicator view overlay

# an empty class to attach to the hitbox PhysAABB
class PlayerHitboxShim:
    def on_damage(self, damage: int, hit_pos: Vec3) -> None:
        if SpsState.cheat_nodmg:
            return

        p_take_damage(damage)

def p_reset():
    SpsState.p_health = 100
    SpsState.p_ammo = 15

    # TODO: SpsState.p_active_view_mesh

    SpsState.p_hitbox = PhysAABB.make(SpsState.p_active_controller.p_pos + Vec3(0., SpsState.p_active_controller.PLAYER_SIZE.y / 2, 0.), SpsState.p_active_controller.PLAYER_SIZE, PlayerHitboxShim())
    
    SpsState.hitbox_scene.add_coll(SpsState.p_hitbox)
    seq.next(p_tick)

def p_tick():
    SpsState.p_hitbox.update(SpsState.p_active_controller.p_pos + Vec3(0., SpsState.p_active_controller.PLAYER_SIZE.y / 2, 0.), SpsState.p_active_controller.PLAYER_SIZE)
    seq.next(p_tick)

def on_map_load() -> None:
    SpsState.dev_con = False

    # crunch filled nightmares
    if os.path.basename(GameState.current_map) == "main_menu.json":
        SpsState.p_hud_ui = MenuUI()
    
    else:
        SpsState.p_hud_ui = GameUI()

    p_reset()

    GameState.static_sequencer.on_event(cue_map.map_load_evid, on_map_load)
GameState.static_sequencer.on_event(cue_map.map_load_evid, on_map_load)