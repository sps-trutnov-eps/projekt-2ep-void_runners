import os

from engine.cue.cue_state import GameState
from engine.cue import cue_sequence as seq
from engine.cue import cue_map
from engine.cue.phys.cue_phys_types import PhysAABB, PhysRay
from engine.cue import cue_utils
from engine.cue.rendering import cue_gizmos as gizmo

from sps_state import SpsState
import prefabs

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

    prefabs.spawn_prefab_from_file("p_view_model", "prefabs/view_models/glock_19.json")
    glock_init()

    seq.next(p_tick)

    GameState.static_sequencer.on_event(cue_map.map_load_evid, p_setup)
GameState.static_sequencer.on_event(cue_map.map_load_evid, p_setup)

def p_tick():
    if SpsState.p_health == 0:
        return

    SpsState.p_hitbox.update(SpsState.p_active_controller.p_pos + Vec3(0., SpsState.p_active_controller.PLAYER_SIZE.y / 2, 0.), SpsState.p_active_controller.PLAYER_SIZE)
    SpsState.hitbox_scene.update_coll(SpsState.p_hitbox)

    glock_tick()

    seq.next(p_tick)

# == glock 19 ==

def glock_init():
    SpsState.p_hud_view_mesh = GameState.entity_storage.get_entity("sps_view_mesh", "p_view_model")
    SpsState.p_hud_view_initial_pos = SpsState.p_hud_view_mesh.view_space_trans._pos

    SpsState.glock_fire_cooldown = 0.
    SpsState.glock_view_knockback = Vec3()

def glock_tick():
    mb = pg.mouse.get_pressed()

    if mb[0] and GameState.current_time - SpsState.glock_fire_cooldown > .25:
        SpsState.glock_fire_cooldown = GameState.current_time
        SpsState.glock_view_knockback = Vec3(0., 0., .2)

        forward_dir = SpsState.p_active_controller.view_forward

        fire_pos = SpsState.p_active_controller.p_pos + SpsState.p_active_controller.CAMERA_OFFSET
        fire_pos += forward_dir # * min(SpsState.p_active_controller.PLAYER_SIZE.x / forward_dir.x, SpsState.p_active_controller.PLAYER_SIZE.y / forward_dir.y, SpsState.p_active_controller.PLAYER_SIZE.z / forward_dir.z)

        fire_ray = PhysRay.make(fire_pos, SpsState.p_active_controller.view_forward)

        coll_hit = GameState.collider_scene.first_hit(fire_ray)
        box_hit = SpsState.hitbox_scene.first_hit(fire_ray, float('inf') if coll_hit is None else coll_hit.tmin)

        if box_hit is not None:
            gizmo.draw_line(SpsState.p_active_controller.p_pos + SpsState.p_active_controller.CAMERA_OFFSET + Vec3(.0, -.1, 0.), Vec3(*box_hit.pos), Vec3(.15, 1., .15), Vec3(.15, 1., .15))
            box_hit.usr.on_damage(1000., Vec3(*box_hit.pos))

        elif coll_hit is not None:
            gizmo.draw_line(SpsState.p_active_controller.p_pos + SpsState.p_active_controller.CAMERA_OFFSET + Vec3(.0, -.1, 0.), Vec3(*coll_hit.pos), Vec3(1., .15, .15), Vec3(1., .15, .15))

        # TODO: fire plasma beam

    SpsState.glock_view_knockback /= 1. + (20. * GameState.delta_time)
    SpsState.p_hud_view_mesh.view_space_trans.set_pos(SpsState.p_hud_view_initial_pos + SpsState.glock_view_knockback)