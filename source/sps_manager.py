import os

from engine.cue.cue_state import GameState
from engine.cue import cue_sequence as seq
from engine.cue import cue_map
from engine.cue.phys.cue_phys_types import PhysAABB
from engine.cue import cue_utils
from engine.cue.rendering import cue_gizmos as gizmo

from ui import GameUI
from sps_state import SpsState
from mainmenu import MenuUI
import prefabs

from pygame.math import Vector3 as Vec3
import pygame as pg

# == global callbacks for managing the game (and player) as a whole ==

def p_respawn_cb(e) -> None:
    # any key, don't care

    if GameState.current_time - SpsState.p_death_timestamp > 1.2: # long enough that people don't get confused, but short enough to not get anoying (hopefully)
        cue_map.load_map_when_safe(GameState.current_map) # reload
    
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
    # reset player state (TODO: add ability stats)

    SpsState.p_health = 100
    SpsState.p_ammo = 15

    # init hitbox and view model
    SpsState.p_hitbox = PhysAABB.make(SpsState.p_active_controller.p_pos + Vec3(0., SpsState.p_active_controller.PLAYER_SIZE.y / 2, 0.), SpsState.p_active_controller.PLAYER_SIZE, PlayerHitboxShim())
    SpsState.hitbox_scene.add_coll(SpsState.p_hitbox)

    prefabs.spawn_prefab_from_file("p_view_model", "prefabs/view_models/glock_19.json")

    seq.next(p_tick)

def p_tick():
    SpsState.p_hitbox.update(SpsState.p_active_controller.p_pos + Vec3(0., SpsState.p_active_controller.PLAYER_SIZE.y / 2, 0.), SpsState.p_active_controller.PLAYER_SIZE)
    SpsState.hitbox_scene.update_coll(SpsState.p_hitbox)

    if SpsState.is_dev_con_open:
        SpsState.is_dev_con_open = cue_utils.show_developer_console()

        # with dev_utils.utils.begin_dev_overlay("tonemap_settings", 2):
        #     _, tonemap_pass.bloom_enabled = imgui.checkbox("Bloom enabled", tonemap_pass.bloom_enabled)
        #     _, tonemap_pass.bloom_strength = imgui.drag_float("Bloom strength", tonemap_pass.bloom_strength, change_speed=0.01)
# 
        #     _, tonemap_pass.exposure = imgui.drag_float("Exposure", tonemap_pass.exposure, change_speed=0.01)

        if not SpsState.is_dev_con_open:
            SpsState.p_active_controller.set_captured(True)

    if SpsState.is_perf_overlay_open:
        cue_utils.show_perf_overlay()

    if SpsState.dev_vis_sub_zones:
        def recursive_subscene_view(scene, i) -> None:
            if SpsState.dev_vis_sub_zone_target is None:
                if scene.sub_aabb is not None:
                    min_p = Vec3(*scene.sub_aabb.points[0])
                    max_p = Vec3(*scene.sub_aabb.points[1])

                    import math
                    gizmo.draw_box(min_p, max_p, Vec3(.35, 1., .35) * math.pow(1.15, -i))
                    gizmo.draw_text(Vec3(*((scene.sub_aabb.points[0] + scene.sub_aabb.points[1]) / 2)), scene.sub_id, Vec3(1., 1., 1.), 20., 30.)

                for sub in scene.child_subscenes.values():
                    recursive_subscene_view(sub, i + 1)
            else:
                if SpsState.dev_vis_sub_zone_target in scene.sub_id:
                    for box in scene.scene_aabbs:
                        min_p = Vec3(*box.points[0])
                        max_p = Vec3(*box.points[1])

                        gizmo.draw_box(min_p, max_p, Vec3(.35, 1., .35))

                for sub in scene.child_subscenes.values():
                    recursive_subscene_view(sub, i + 1)

        recursive_subscene_view(GameState.collider_scene, 0)

    seq.next(p_tick)

def on_map_load() -> None:
    SpsState.is_dev_con_open = False

    # crunch filled nightmares
    if os.path.basename(GameState.current_map) == "main_menu.json":
        SpsState.p_hud_ui = MenuUI()
    
    else:
        SpsState.p_hud_ui = GameUI()
        p_reset()

    GameState.static_sequencer.on_event(cue_map.map_load_evid, on_map_load)
GameState.static_sequencer.on_event(cue_map.map_load_evid, on_map_load)