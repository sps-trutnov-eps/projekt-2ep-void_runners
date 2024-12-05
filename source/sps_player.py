from dataclasses import dataclass
import os

from engine.cue.cue_state import GameState
from engine.cue import cue_sequence as seq
from engine.cue import cue_map
from engine.cue.phys.cue_phys_types import PhysAABB

from sps_state import SpsState
from sps_weapons import FdevImpl, GlockImpl

from pygame.math import Vector3 as Vec3
import pygame as pg

# == top-level player code ==

def p_respawn_cb(e) -> None:
    # any key, don't care

    if GameState.current_time - SpsState.p_death_timestamp > 1.2: # long enough that people don't get confused, but short enough to not get anoying (hopefully)
        cue_map.load_map_when_safe(GameState.current_map) # reload
    
    else:
        seq.on_event(pg.KEYDOWN, p_respawn_cb) # too early, wait for another key later

def p_death() -> None:
    SpsState.p_health = 0

    SpsState.p_active_controller.movement_disabled = True
    SpsState.p_active_controller.view_overlay_pos = Vec3(0., -SpsState.p_active_controller.PLAYER_SIZE.y * .6, 0.)

    SpsState.p_death_timestamp = GameState.current_time

    GameState.entity_storage.despawn("p_view_model")    
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

    def on_force(self, active_force: Vec3) -> None:
        SpsState.p_active_controller.p_vel += active_force * GameState.delta_time

def p_setup():
    if os.path.basename(GameState.current_map) == "main_menu.json":
        GameState.static_sequencer.on_event(cue_map.map_load_evid, p_setup)
        return
    
    # reset player state (TODO: add ability stats)

    SpsState.p_health = 100
    SpsState.p_ammo = 15

    # init hitbox and view model
    SpsState.p_hitbox = PhysAABB.make(SpsState.p_active_controller.p_pos + Vec3(0., SpsState.p_active_controller.PLAYER_SIZE.y / 2, 0.), SpsState.p_active_controller.PLAYER_SIZE, PlayerHitboxShim())
    SpsState.hitbox_scene.add_coll(SpsState.p_hitbox)

    SpsState.p_weapon_impl = GlockImpl()

    seq.next(p_tick)

    GameState.static_sequencer.on_event(cue_map.map_load_evid, p_setup)
GameState.static_sequencer.on_event(cue_map.map_load_evid, p_setup)

def p_tick():
    if SpsState.p_health == 0:
        return

    SpsState.p_hitbox.update(SpsState.p_active_controller.p_pos + Vec3(0., SpsState.p_active_controller.PLAYER_SIZE.y / 2, 0.), SpsState.p_active_controller.PLAYER_SIZE)
    SpsState.hitbox_scene.update_coll(SpsState.p_hitbox)

    SpsState.p_weapon_impl.tick()

    seq.next(p_tick)