from dataclasses import dataclass

from engine.cue.entities import cue_entity_types as en
from engine.cue.rendering import cue_gizmos as gizmo

from engine.cue.cue_state import GameState
from engine.cue.components.cue_transform import Transform
from engine.cue.rendering.cue_camera import Camera
from engine.cue.entities.cue_entity_utils import handle_transform_edit_mode

from pygame.math import Vector3 as Vec3, Vector2 as Vec2

import pygame as pg
import numpy as np

# a map entity for specifying the player spawn position

@dataclass(init=False, slots=True)
class SpsStaticCam:
    def __init__(self, en_data: dict) -> None:
        self.cam = Camera(GameState.renderer.win_aspect)
        self.cam.set_view(en_data["t_pos"], Vec3(en_data["t_rot"].x, en_data["t_rot"].y, 0.))

        GameState.active_camera = self.cam

    trans: Transform
    cam: Camera

def spawn_player_point(en_data: dict):
    return SpsStaticCam(en_data)

def dev_player_spawn(s: dict | None, dev_state: dict, en_data: dict) -> dict:
    if s is None or not s["last_dict"] == en_data:
        if en_data["t_pos"] is None:
            en_data["t_pos"] = dev_state["suggested_initial_pos"]

        s = {
            "last_dict": dict(en_data),
            "trans": Transform(en_data["t_pos"], Vec3(en_data["t_rot"].x, -en_data["t_rot"].y, 0.)),
        }

    if dev_state["is_selected"]:
        # handle trasnsform editing
        handle_transform_edit_mode(s, dev_state, en_data, True, False, False)
    
    pos = en_data["t_pos"]
    min_p = pos - Vec3(.15, .15, .15)
    max_p = pos + Vec3(.15, .15, .15)
    line_col = Vec3(1., 1., .2) if dev_state["is_selected"] else Vec3(.7, .7, .05)

    gizmo.draw_box(min_p, max_p, line_col)

    # create a quad of points transformed by the cam pos and rot
    quad = [
        (s["trans"]._trans_matrix @ np.array((.2, .2, -.4, 1.), dtype=np.float32))[:3],
        (s["trans"]._trans_matrix @ np.array((-.2, .2, -.4, 1.), dtype=np.float32))[:3],
        (s["trans"]._trans_matrix @ np.array((-.2, -.2, -.4, 1.), dtype=np.float32))[:3],
        (s["trans"]._trans_matrix @ np.array((.2, -.2, -.4, 1.), dtype=np.float32))[:3],
    ]

    for i in range(4):
        gizmo.draw_line(quad[i], quad[(i + 1) % 4], line_col, line_col)

    return s

def gen_def_data():
    return {
        "t_pos": None,
        "t_rot": Vec2(),
    }

en.create_entity_type("sps_static_cam", spawn_player_point, None, dev_player_spawn, gen_def_data)