import time, os, sys, argparse

try:
    from engine.cue.cue_state import GameState

    from engine.cue.cue_sequence import CueSequencer
    from engine.cue.cue_entity_storage import EntityStorage
    from engine.cue.cue_assets import AssetManager

    from engine.cue.rendering.cue_renderer import CueRenderer
    from engine.cue.rendering.cue_scene import RenderScene

    from engine.cue import cue_map
    from engine.cue import cue_utils
    from engine.cue import cue_cmds
    from engine.cue import cue_sequence as seq

    from engine.cue.phys.cue_phys_scene import PhysScene

except ImportError: 
    print("[\x1b[1m\x1b[31merror\x1b[0m] There was a problem importing the Cue Engine, make sure you pip installed the requirements.txt and did a `git submodule update --init`")
    raise

import pygame as pg
import numpy as np
import imgui

# == contants ==

ASSET_DIR = os.path.join(os.path.dirname(__file__), "../assets/")
BOOTUP_MAP =  ASSET_DIR + "/maps/test_map2.json"

# == launch arguments ==

p = argparse.ArgumentParser()
p.add_argument("--bmap", type=str, dest="bootup_map")

args = p.parse_args()

if args.bootup_map:
    BOOTUP_MAP = args.bootup_map

# == import game code ==

import entity.sps_player_spawn
import entity.sps_static_cam
import entity.sps_dev_text
import entity.sps_view_mesh

import dev_utils
from ui import GameUI
from sps_state import SpsState

# == init engine ==

t = time.perf_counter()

GameState.sequencer = CueSequencer(t)
GameState.static_sequencer = CueSequencer(t)
GameState.entity_storage = EntityStorage()
GameState.asset_manager = AssetManager(ASSET_DIR)

GameState.renderer = CueRenderer((1280, 720), fullscreen=False, vsync=True)
GameState.active_scene = RenderScene()
GameState.collider_scene = PhysScene()

# == Init game state ==

SpsState.p_hud_ui = GameUI(lives=3, ammo=50, score=0)

def on_map_load(path: str) -> None:
    SpsState.dev_con = False

    # try to lookup the player spawn entity
    try:
        SpsState.p_active_controller = GameState.entity_storage.get_entity("sps_player_spawn", "sps_player").player_controller
    except KeyError:
        SpsState.p_active_controller = None

    # GameState.static_sequencer.on_event(cue_map.on_load_evid, on_map_load)
# GameState.static_sequencer.on_event(cue_map.on_load_evid, on_map_load)

# == init map ==

cue_map.load_map(BOOTUP_MAP)
on_map_load(BOOTUP_MAP)

# == main game loop ==

while True:
    # == event poll ==

    for e in pg.event.get():
        GameState.renderer.fullscreen_imgui_ctx.process_key_event(e)

        if e.type == pg.MOUSEMOTION:
            GameState.renderer.fullscreen_imgui_ctx.set_mouse_input(e.pos)

        if e.type == pg.KEYDOWN and e.dict["key"] == pg.K_ESCAPE:
            SpsState.dev_con ^= True
            SpsState.p_active_controller.set_captured(not SpsState.dev_con)

        if e.type == pg.QUIT:
            sys.exit(0)

        GameState.sequencer.send_event_id(e.type, e)
        GameState.static_sequencer.send_event_id(e.type, e)

    # == tick ==

    dt = (time.perf_counter() - t) * dev_utils.dev_deltascale
    t = time.perf_counter()

    GameState.delta_time = dt
    GameState.renderer.fullscreen_imgui_ctx.delta_time(dt)

    GameState.renderer.fullscreen_imgui_ctx.set_as_current_context()
    imgui.new_frame()
    
    GameState.sequencer.tick(t)
    GameState.static_sequencer.tick(t)

    tt = time.perf_counter() - t

    # == frame ==

    SpsState.p_hud_ui.render_ui()

    if SpsState.dev_con:
        SpsState.dev_con = cue_utils.show_developer_console()

        if not SpsState.dev_con:
            SpsState.p_active_controller.set_captured(True)

    if dev_utils.is_perf_overlay_open:
        cue_utils.show_perf_overlay()

    GameState.renderer.frame(GameState.active_camera, GameState.active_scene)

    GameState.cpu_tick_time = tt # delayed by a frame to match cpu_render_time
    GameState.cpu_render_time = GameState.renderer.cpu_frame_time