from dataclasses import dataclass

from engine.cue.entities import cue_entity_types as en
from engine.cue.rendering import cue_gizmos as gizmo

from engine.cue.cue_state import GameState
from engine.cue.components.cue_transform import Transform

from engine.cue.rendering.cue_camera import Camera
from components.player_move import PlayerMovement

from pygame.math import Vector3 as Vec3, Vector2 as Vec2

# a map entity for specifying the player spawn position

@dataclass(init=False, slots=True)
class SpsPlayerSpawn:
    def __init__(self, en_data: dict) -> None:
        GameState.active_camera = Camera(GameState.renderer.win_aspect)

        self.player_controller = PlayerMovement(Transform(en_data["spawn_pos"], Vec3(0., 0., 0.)), GameState.active_camera, en_data["spawn_rot"])
    
    player_controller: PlayerMovement

def spawn_player_point(en_data: dict):
    return SpsPlayerSpawn(en_data)

def dev_player_spawn(s: None, dev_state: dict, en_data: dict) -> None:
    min_p = en_data["spawn_pos"] - PlayerMovement.PLAYER_SIZE / 2
    max_p = en_data["spawn_pos"] + PlayerMovement.PLAYER_SIZE / 2

    min_p.y += PlayerMovement.PLAYER_SIZE.y / 2
    max_p.y += PlayerMovement.PLAYER_SIZE.y / 2
    
    gizmo.draw_box(min_p, max_p, Vec3(1., 1., .2) if dev_state["is_selected"] else Vec3(.7, .7, .05))

def gen_def_data():
    return {
        "spawn_pos": Vec3(),
        "spawn_rot": Vec2(),
    }

en.create_entity_type("sps_player_spawn", spawn_player_point, None, dev_player_spawn, gen_def_data)