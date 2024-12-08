import time, os, sys, argparse

try:
    from engine.cue.cue_state import GameState

    from engine.cue.cue_sequence import CueSequencer
    from engine.cue.cue_entity_storage import EntityStorage
    from engine.cue.cue_assets import AssetManager

    from engine.cue.rendering.cue_renderer import CueRenderer
    from engine.cue.rendering.cue_scene import RenderScene

    from engine.cue import cue_map
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
BOOTUP_MAP =  ASSET_DIR + "/maps/main_menu.json"

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
import entity.sps_hurt_trigger
import entity.sps_static_fire

import entity.sps_projectile
import entity.sps_spawner
import entity.sps_hitbox_ai
import entity.sps_nav_node

from sps_state import SpsState
import dev_utils
import sps_manager
import sps_player

# == init engine ==

GameState.current_time = time.perf_counter()

GameState.sequencer = CueSequencer(GameState.current_time)
GameState.entity_storage = EntityStorage()
GameState.asset_manager = AssetManager(ASSET_DIR)

GameState.renderer = CueRenderer((1280, 720), fullscreen=False, vsync=True)
GameState.active_scene = RenderScene()
GameState.collider_scene = PhysScene()
GameState.trigger_scene = PhysScene()

# == Init game state ==

SpsState.hitbox_scene = PhysScene()
cue_map.load_map(BOOTUP_MAP)

from sps_post_pass import BloomPostPass, TonemapPostPass
SpsState.tonemap_post_pass = TonemapPostPass()

GameState.renderer.activate_post_pass(BloomPostPass(GameState.renderer.win_res))
GameState.renderer.activate_post_pass(SpsState.tonemap_post_pass)

pg.display.set_caption("Void Runners")

# == main game loop ==

while True:
    # == event poll ==

    for e in pg.event.get():
        GameState.renderer.fullscreen_imgui_ctx.process_key_event(e)

        if e.type == pg.MOUSEMOTION:
            GameState.renderer.fullscreen_imgui_ctx.set_mouse_input(e.pos)

        if e.type == pg.KEYDOWN and e.dict["key"] == pg.K_ESCAPE:
            SpsState.is_dev_con_open ^= True
            SpsState.p_active_controller.set_captured(not SpsState.is_dev_con_open)

        if e.type == pg.QUIT:
            sys.exit(0)

        GameState.sequencer.send_event_id(e.type, e)
        GameState.static_sequencer.send_event_id(e.type, e)

    # check for deferred map loads
    if hasattr(GameState, "next_map_deferred"):
        cue_map.load_map(GameState.next_map_deferred)

    # == tick ==

    dt = (time.perf_counter() - GameState.current_time) * SpsState.cheat_deltascale
    GameState.current_time = time.perf_counter()

    GameState.delta_time = dt
    GameState.renderer.fullscreen_imgui_ctx.delta_time(dt)

    GameState.renderer.fullscreen_imgui_ctx.set_as_current_context()
    imgui.new_frame()

    GameState.sequencer.tick(GameState.current_time)
    GameState.static_sequencer.tick(GameState.current_time)

    tt = time.perf_counter() - GameState.current_time

    # == frame ==

    SpsState.p_hud_ui.render_ui()

    GameState.renderer.frame(GameState.active_camera, GameState.active_scene)

    GameState.cpu_tick_time = tt # delayed by a frame to match cpu_render_time
    GameState.cpu_render_time = GameState.renderer.cpu_frame_time