import os

from engine.cue.cue_state import GameState
from engine.cue import cue_sequence as seq
from engine.cue import cue_map
from engine.cue import cue_utils
from engine.cue.rendering import cue_gizmos as gizmo

from ui import GameUI
from sps_state import SpsState
from mainmenu import MenuUI

import dev_utils

from pygame.math import Vector3 as Vec3
import imgui

# == global callbacks for managing the game (and player) as a whole ==

def m_setup():
    seq.next(m_tick)

def m_tick():
    if SpsState.is_dev_con_open:
        SpsState.is_dev_con_open = cue_utils.show_developer_console()

        if not SpsState.is_dev_con_open:
            SpsState.p_active_controller.set_captured(True)

        if SpsState.is_post_config_open:
            with dev_utils.utils.begin_dev_overlay("tonemap_settings", 2):
                _, SpsState.tonemap_post_pass.bloom_enabled = imgui.checkbox("Bloom enabled", SpsState.tonemap_post_pass.bloom_enabled)
                _, SpsState.tonemap_post_pass.bloom_strength = imgui.drag_float("Bloom strength", SpsState.tonemap_post_pass.bloom_strength, change_speed=0.01)

                _, SpsState.tonemap_post_pass.exposure = imgui.drag_float("Exposure", SpsState.tonemap_post_pass.exposure, change_speed=0.01)

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

    seq.next(m_tick)

    # enable map trigger when all enemies are dead

    if (hasattr(SpsState, "active_enemy_count") and SpsState.active_enemy_count == 0) or SpsState.p_selected_char == "Speedrunner":
        try:
            map_trig = GameState.entity_storage.get_entity("bt_map_trigger", "map_exit_trigger")
            map_trig.is_enabled = True
            
        except KeyError:
            pass # in a map with no exit trigger

def on_map_reset() -> None:
    SpsState.hitbox_scene.reset()
    SpsState.active_nav_nodes = []
    SpsState.active_drone_count = 0
    SpsState.active_enemy_count = 0

    GameState.static_sequencer.on_event(cue_map.map_reset_evid, on_map_reset)
GameState.static_sequencer.on_event(cue_map.map_reset_evid, on_map_reset)

def on_map_load() -> None:
    SpsState.is_dev_con_open = False
    m_setup()

    # crunch filled nightmares
    if os.path.basename(GameState.current_map) == "main_menu.json":
        SpsState.p_hud_ui = MenuUI()
    
    else:
        SpsState.p_hud_ui = GameUI()

    GameState.static_sequencer.on_event(cue_map.map_load_evid, on_map_load)
GameState.static_sequencer.on_event(cue_map.map_load_evid, on_map_load)