import time

from dataclasses import dataclass
from engine.cue.entities import cue_entity_types as en
from engine.cue.cue_state import GameState
from sps_state import SpsState
import sps_player as player

from engine.cue.components.cue_transform import Transform
from engine.cue.phys.cue_phys_types import PhysAABB

from engine.cue.rendering import cue_gizmos as gizmo

from pygame.math import Vector3 as Vec3
from engine.cue.entities.cue_entity_utils import handle_transform_edit_mode

# a trigger box entity for triggering map loads / transitions

@dataclass(init=False, slots=True)
class SpsHurtTrigger:
    def __init__(self, en_data: dict) -> None:
        self.aabb = PhysAABB.make(en_data["t_pos"], en_data["t_scale"], self)
        GameState.trigger_scene.add_coll(self.aabb)
        
        self.hurt_damage = int(en_data["hurt_damage"])
        self.hurt_interval = en_data["hurt_interval"]

        self.last_damage_time = 0

    def on_triggered(self) -> None:
        if self.hurt_interval == 0.:
            player.p_death()
            return

        if time.perf_counter() - self.last_damage_time > self.hurt_interval:
            player.p_take_damage(self.hurt_damage)
            self.last_damage_time = time.perf_counter()

    # == entity hooks ==

    @staticmethod
    def spawn(en_data: dict) -> 'SpsHurtTrigger':
        return SpsHurtTrigger(en_data)

    def despawn(self) -> None:
        GameState.trigger_scene.remove_coll(self.aabb)

    @staticmethod
    def dev_tick(s: dict | None, dev_state: en.DevTickState, en_data: dict) -> dict:
        if s is None:
            # init aabb editor

            if en_data["t_pos"] is None:
                en_data["t_pos"] = dev_state.suggested_initial_pos

            s = {"aabb_t": Transform(en_data["t_pos"], Vec3(0., 0., 0.), en_data["t_scale"]), "last_data": dict(en_data)}
        elif en_data != s["last_data"]:
            s["aabb_t"] = Transform(en_data["t_pos"], Vec3(0., 0., 0.), en_data["t_scale"])
            s["last_data"] = dict(en_data)

        # handle edit mode

        if dev_state.is_entity_selected:
            handle_transform_edit_mode(s, dev_state, en_data)

        # draw trigger gizmo

        t = s["aabb_t"]

        min_p = t._pos - t._scale / 2
        max_p = t._pos + t._scale / 2

        line_col = Vec3(1., .15, .15) if dev_state.is_entity_selected else Vec3(.6, .08, .08)
        gizmo.draw_box(min_p, max_p, line_col)

        return s

    aabb: PhysAABB

    hurt_damage: int
    hurt_interval: float

    last_damage_time: float

def gen_def_data() -> dict:
    return {
        "t_pos": None,
        "t_scale": Vec3(2., 2., 2.),
        "hurt_damage": 15,
        "hurt_interval": .25, # set to 0 to make it a kill trigger
    }

en.create_entity_type("sps_hurt_trigger", SpsHurtTrigger.spawn, SpsHurtTrigger.despawn, SpsHurtTrigger.dev_tick, gen_def_data)