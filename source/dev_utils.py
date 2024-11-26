from engine.cue.cue_state import GameState
from engine.cue.cue_map import reset_state
import engine.cue.cue_utils as utils
from sps_state import SpsState

from pygame.math import Vector3 as Vec3, Vector2 as Vec2
import random

def gen_map(args: list[str]):
    try:
        ball_count: int = 2000 if len(args) < 1 else int(args[0])
        min_p: int = -20 if len(args) < 2 else int(args[1])
        max_p: int = 20 if len(args) < 3 else int(args[2])
    except:
        utils.error("failed to parse args, use 'gen_map [ball_count] [min_coord] [max_coord]'")
        return

    utils.info("[dev utils] generating and loading a benchmark map...")
    
    reset_state()
    GameState.entity_storage.spawn("sps_player_spawn", "p_spawn", {"t_pos": Vec3(0., 0., 0.), "spawn_rot": Vec2(0., 0.)})

    for i in range(ball_count):
        ball_data = {
            "t_pos": Vec3([random.randint(min_p, max_p), random.randint(min_p, max_p), random.randint(min_p, max_p)]),
            "t_rot": Vec3([0.0, 0.0, 0.0]),
            "t_scale": Vec3([1.0, 1.0, 1.0]),
            "a_model_mesh": "models/icosph.npz",
            "a_model_vshader": "shaders/base_cam.vert",
            "a_model_fshader": "shaders/basic_lit.frag",
        }

        GameState.entity_storage.spawn("bt_static_mesh", f"b{i}", ball_data)

# register a dev console command
utils.add_dev_command("gen_map", gen_map)

# == player info overlay ==

def player_info_cmd(args: list[str]):
    try:
        p_spawn = GameState.entity_storage.get_entity("sps_player_spawn", "sps_player")
    except KeyError:
        utils.error("[dev utils] No active player controller, can't show info")
        return

    p_spawn.player_controller.show_player_info ^= True

utils.add_dev_command("player_info", player_info_cmd)

# == player debug toggle ==

def player_debug_cmd(args: list[str]):
    try:
        p_spawn = GameState.entity_storage.get_entity("sps_player_spawn", "sps_player")
    except KeyError:
        utils.error("[dev utils] No active player controller, can't show debug")
        return

    p_spawn.player_controller.show_player_debug ^= True

utils.add_dev_command("player_debug", player_debug_cmd)

# == perf overlay ==

is_perf_overlay_open = False
def perf_overlay_cmd(args: list[str]):
    global is_perf_overlay_open
    is_perf_overlay_open ^= True

utils.add_dev_command("perf_info", perf_overlay_cmd)

# == deltascale ==

dev_deltascale = 1.
def deltascale_cmd(args: list[str]):
    if len(args) != 1:
        utils.error("[dev utils] unknown args, use 'deltascale [deltascale_scalar]' to set deltascale")
        return

    try:
        scale = float(args[0])
    except:
        utils.error("[dev utils] unknown deltascale value")
        return

    utils.info(f"[dev utils] setting deltascale to {scale}")
    
    global dev_deltascale
    dev_deltascale = scale

utils.add_dev_command("deltascale", deltascale_cmd)

# == ai cmds ==

def ai_debug_cmd(args: list[str]):
    SpsState.ai_debug ^= True

utils.add_dev_command("ai_debug", ai_debug_cmd)