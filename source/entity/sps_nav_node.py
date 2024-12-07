import time

from dataclasses import dataclass
from engine.cue.entities import cue_entity_types as en
from engine.cue.cue_state import GameState
from sps_state import SpsState
import sps_manager as manag

from engine.cue.components.cue_transform import Transform
from engine.cue.phys.cue_phys_types import PhysAABB

from engine.cue.rendering import cue_gizmos as gizmo

from pygame.math import Vector3 as Vec3
from engine.cue.entities.cue_entity_utils import handle_transform_edit_mode

# an invisible node for use by the ai drone navigation and patrolling

@dataclass(init=False, slots=True)
class SpsNavNode:
    def __init__(self, en_data: dict) -> None:
        self.node_pos = en_data["t_pos"]
        SpsState.active_nav_nodes.append(self)

    # == entity hooks ==

    @staticmethod
    def spawn(en_data: dict) -> 'SpsNavNode':
        return SpsNavNode(en_data)

    def despawn(self) -> None:
        GameState.trigger_scene.remove_coll(self.aabb)

    @staticmethod
    def dev_tick(s: dict | None, dev_state: en.DevTickState, en_data: dict) -> dict:
        if s is None:
            if en_data["t_pos"] is None:
                en_data["t_pos"] = dev_state.suggested_initial_pos

            s = {"node_t": Transform(en_data["t_pos"], Vec3(0., 0., 0.)), "last_data": dict(en_data)}
        elif en_data != s["last_data"]:
            s["node_t"] = Transform(en_data["t_pos"], Vec3(0., 0., 0.))
            s["last_data"] = dict(en_data)

        # handle edit mode

        if dev_state.is_entity_selected:
            handle_transform_edit_mode(s, dev_state, en_data)

        # draw trigger gizmo

        t = s["node_t"]

        pos = t._pos

        line_col = Vec3(.15, .65, 1.) if dev_state.is_entity_selected else Vec3(.08, .15, .6)
        gizmo.draw_line(pos + Vec3(.1, .0, .0), pos - Vec3(.1, .0, .0), line_col, line_col)
        gizmo.draw_line(pos + Vec3(.0, .1, .0), pos - Vec3(.0, .1, .0), line_col, line_col)
        gizmo.draw_line(pos + Vec3(.0, .0, .1), pos - Vec3(.0, .0, .1), line_col, line_col)

        return s

    node_pos: Vec3

def gen_def_data() -> dict:
    return {
        "t_pos": None,
    }

en.create_entity_type("sps_nav_node", SpsNavNode.spawn, SpsNavNode.despawn, SpsNavNode.dev_tick, gen_def_data)