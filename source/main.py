import time, os, sys

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

    from ui import GameUI

    import pygame as pg
    import imgui

except ImportError: 
    print("[\x1b[1m\x1b[31merror\x1b[0m] There was a problem importing the Cue Engine, make sure you pip installed the requirements.txt and did a `git submodule update --init`")
    raise

# == contants ==

ASSET_DIR = os.path.join(os.path.dirname(__file__), "../assets")
BOOTUP_MAP = "/maps/test_map2.json"

# == import game entities ==

import entity.sps_player_spawn
import entity.sps_static_cam

import dev_utils

# == init engine ==

t = time.perf_counter()

GameState.sequencer = CueSequencer(t)
GameState.static_sequencer = CueSequencer(t)
GameState.entity_storage = EntityStorage()
GameState.asset_manager = AssetManager(ASSET_DIR)

GameState.renderer = CueRenderer((1280, 720), fullscreen=False, vsync=True)
GameState.active_scene = RenderScene()

# == Init game state ==

game_ui = GameUI(lives=3, ammo=50, score=0)
dev_con = False

p_spawn: entity.sps_player_spawn.SpsPlayerSpawn | None = None

def on_map_load(path: str) -> None:
    global p_spawn

    # try to lookup the player spawn entity
    try:
        p_spawn = GameState.entity_storage.get_entity("sps_player_spawn", "sps_player")
    except KeyError:
        p_spawn = None

    # GameState.static_sequencer.on_event(cue_map.on_load_evid, on_map_load)
# GameState.static_sequencer.on_event(cue_map.on_load_evid, on_map_load)

# == init map ==

cue_map.load_map(ASSET_DIR + BOOTUP_MAP)
on_map_load(ASSET_DIR + BOOTUP_MAP)

# == main game loop ==

while True:
    # == event poll ==

    for e in pg.event.get():
        GameState.renderer.fullscreen_imgui_ctx.process_key_event(e)

        if e.type == pg.MOUSEMOTION:
            GameState.renderer.fullscreen_imgui_ctx.set_mouse_input(e.pos)

        if e.type == pg.KEYDOWN and e.dict["key"] == pg.K_BACKQUOTE:
            dev_con ^= True
            p_spawn.player_controller.set_captured(not dev_con)

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

    if dev_con:
        dev_con = cue_utils.show_developer_console()

        if not dev_con:
            p_spawn.player_controller.set_captured(True)

    if dev_utils.is_perf_overlay_open:
        cue_utils.show_perf_overlay()

    GameState.renderer.frame(GameState.active_camera, GameState.active_scene)

    GameState.cpu_tick_time = tt # delayed by a frame to match cpu_render_time
    GameState.cpu_render_time = GameState.renderer.cpu_frame_time