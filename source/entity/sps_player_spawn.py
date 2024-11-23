from dataclasses import dataclass

from engine.cue.entities import cue_entity_types as en
from engine.cue.rendering import cue_gizmos as gizmo

from engine.cue.cue_state import GameState
from engine.cue.components.cue_transform import Transform
from engine.cue.rendering.cue_camera import Camera
from engine.cue.entities.cue_entity_utils import handle_transform_edit_mode

from sps_state import SpsState
from components.player_move import PlayerMovement

from pygame.math import Vector3 as Vec3, Vector2 as Vec2

# a map entity for specifying the player spawn position

@dataclass(init=False, slots=True)
class SpsPlayerSpawn:
    def __init__(self, en_data: dict) -> None:
        GameState.active_camera = Camera(GameState.renderer.win_aspect)

        self.player_controller = PlayerMovement(Transform(en_data["t_pos"], Vec3(0., 0., 0.)), GameState.active_camera, en_data["spawn_rot"])
        SpsState.p_active_controller = self.player_controller
    
    # == entity hooks ==

    @staticmethod
    def spawn(en_data: dict) -> 'SpsPlayerSpawn':
        return SpsPlayerSpawn(en_data)

    @staticmethod
    def dev_tick(s: dict | None, dev_state: en.DevTickState, en_data: dict) -> dict:
        if en_data["t_pos"] is None:
            en_data["t_pos"] = dev_state.suggested_initial_pos

        if s is None:
            s = {}

        if dev_state.is_entity_selected:
            # handle trasnsform editing
            handle_transform_edit_mode(s, dev_state, en_data, True, False, False)

        min_p = en_data["t_pos"] - PlayerMovement.PLAYER_SIZE / 2
        max_p = en_data["t_pos"] + PlayerMovement.PLAYER_SIZE / 2

        min_p.y += PlayerMovement.PLAYER_SIZE.y / 2
        max_p.y += PlayerMovement.PLAYER_SIZE.y / 2

        gizmo.draw_box(min_p, max_p, Vec3(1., 1., .2) if dev_state.is_entity_selected else Vec3(.7, .7, .05))

        return s

    player_controller: PlayerMovement

def gen_def_data():
    return {
        "t_pos": None,
        "spawn_rot": Vec2(),
    }

en.create_entity_type("sps_player_spawn", SpsPlayerSpawn.spawn, None, SpsPlayerSpawn.dev_tick, gen_def_data)