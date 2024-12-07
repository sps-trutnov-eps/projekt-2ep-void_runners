from dataclasses import dataclass
from engine.cue.entities import cue_entity_types as en
from engine.cue.rendering import cue_gizmos as gizmo

from components.fire_emitter import FireEmitter

from pygame.math import Vector3 as Vec3
from engine.cue.entities.cue_entity_utils import handle_transform_edit_mode

# a trigger box entity for triggering map loads / transitions

@dataclass(init=False, slots=True)
class SpsStaticFire:
    def __init__(self, en_data: dict) -> None:
        self.fire_emitter = FireEmitter()

        self.fire_emitter.set_origin(en_data["t_pos"])
        self.fire_emitter.set_on_fire(en_data["start_lit"])

    # == entity hooks ==

    @staticmethod
    def spawn(en_data: dict) -> 'SpsStaticFire':
        return SpsStaticFire(en_data)

    def despawn(self) -> None:
        self.fire_emitter.set_on_fire(False)

    @staticmethod
    def dev_tick(s: dict | None, dev_state: en.DevTickState, en_data: dict) -> dict:
        if s is None:
            # init aabb editor

            if en_data["t_pos"] is None:
                en_data["t_pos"] = dev_state.suggested_initial_pos

            s = {"t_pos": en_data["t_pos"], "last_data": dict(en_data)}
        elif en_data != s["last_data"]:
            s["t_pos"] = en_data["t_pos"]
            s["last_data"] = dict(en_data)

        # handle edit mode

        if dev_state.is_entity_selected:
            handle_transform_edit_mode(s, dev_state, en_data, True, False, False)

        # draw trigger gizmo

        pos = s["t_pos"]

        min_p = pos - Vec3(.1)
        max_p = pos + Vec3(.1)

        line_col = Vec3(1., 1., .15) if dev_state.is_entity_selected else Vec3(.6, .6, .08)
        gizmo.draw_box(min_p, max_p, line_col)

        return s

    fire_emitter: FireEmitter

def gen_def_data() -> dict:
    return {
        "t_pos": None,
        "start_lit": True,
    }

en.create_entity_type("sps_static_fire", SpsStaticFire.spawn, SpsStaticFire.despawn, SpsStaticFire.dev_tick, gen_def_data)