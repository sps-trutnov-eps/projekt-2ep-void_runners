from engine.cue.entities import cue_entity_types as en
from engine.cue.rendering import cue_gizmos as gizmo

from engine.cue.entities.cue_entity_utils import handle_transform_edit_mode
from pygame.math import Vector3 as Vec3

def spawn_dev_text(en_data: dict) -> None:
    return None # dev_text only shows itself in the editor

def dev_text_tick(s: dict | None, dev_state: dict, en_data: dict) -> dict:
    if en_data["t_pos"] is None:
        en_data["t_pos"] = dev_state["suggested_initial_pos"]

    if s is None:
        s = {}

    if dev_state["is_selected"]:
        handle_transform_edit_mode(s, dev_state, en_data, True, False, False)

    min_p = en_data["t_pos"] - Vec3(.05, .05, .05)
    max_p = en_data["t_pos"] + Vec3(.05, .05, .05)
    line_col = Vec3(1., .35, 1.)

    gizmo.draw_box(min_p, max_p, line_col)
    if not en_data["hide_text"]:
        gizmo.draw_text(en_data["t_pos"], en_data["dev_text"])

    return s

def gen_def_data() -> dict:
    return {
        "t_pos": None,
        "dev_text": "",
        "hide_text": False,
    }

en.create_entity_type("sps_dev_text", spawn_dev_text, None, dev_text_tick, gen_def_data)