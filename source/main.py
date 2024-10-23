import time, os, sys

try:
    from engine.cue.cue_state import GameState

    from engine.cue.cue_sequence import CueSequencer
    from engine.cue.cue_entity_storage import EntityStorage
    from engine.cue.cue_assets import AssetManager

    from engine.cue.rendering.cue_renderer import CueRenderer
    from engine.cue.rendering.cue_scene import RenderScene

    from engine.cue import cue_map

    from ui import GameUI

    import pygame as pg
    import imgui

except ImportError: 
    print("[\x1b[1m\x1b[31merror\x1b[0m] There was a problem importing the Cue Engine, make sure you pip installed the requirements.txt and did a `git submodule update --init`")
    raise

# == contants ==

ASSET_DIR = os.path.join(os.path.dirname(__file__), "../assets")
BOOTUP_MAP = "/maps/test_map.json"

# == import game entities ==

import entity.sps_player_spawn
import entity.sps_static_cam

# == init engine ==

t = time.perf_counter()

GameState.sequencer = CueSequencer(t)
GameState.static_sequencer = CueSequencer(t)
GameState.entity_storage = EntityStorage()
GameState.asset_manager = AssetManager(ASSET_DIR)

GameState.renderer = CueRenderer((1280, 720), fullscreen=False, vsync=True)

# == init map ==

def clear_map() -> None:
    global t
    t = time.perf_counter()

    GameState.entity_storage.reset()
    GameState.sequencer.reset(t)

    # GameState.asset_manager.reset()
    
    GameState.active_scene = RenderScene()
    # GameState.active_camera = None

clear_map()
cue_map.load_map(ASSET_DIR + BOOTUP_MAP)

# == main game loop ==

# == Init UI ==

game_ui = GameUI(lives=3, ammo=50, score=0)

while True:
    # == event poll ==

    for e in pg.event.get():
        if e.type == pg.QUIT:
            sys.exit(0)

        GameState.sequencer.send_event_id(e.type, e)
        GameState.static_sequencer.send_event_id(e.type, e)

    # == tick ==

    dt = time.perf_counter() - t
    t = time.perf_counter()

    GameState.delta_time = dt
    GameState.renderer.fullscreen_imgui_ctx.delta_time(dt)

    GameState.renderer.fullscreen_imgui_ctx.set_as_current_context()
    imgui.new_frame()
    
    GameState.sequencer.tick(t)
    GameState.static_sequencer.tick(t)

    tt = time.perf_counter() - t

    # == frame ==

    game_ui.render_ui()

    GameState.renderer.frame(GameState.active_camera, GameState.active_scene)

    GameState.cpu_tick_time = tt # delayed by a frame to match cpu_render_time
    GameState.cpu_render_time = GameState.renderer.cpu_frame_time