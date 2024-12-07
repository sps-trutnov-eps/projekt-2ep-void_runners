from dataclasses import dataclass
from engine.cue import cue_sequence as seq
from engine.cue.entities import cue_entity_types as en
from engine.cue.cue_state import GameState

from engine.cue.components.cue_transform import Transform
from engine.cue.components.cue_model import ModelRenderer
from engine.cue.rendering.cue_camera import Camera

from pygame.math import Vector3 as Vec3, Vector2 as Vec2
from engine.cue.entities.cue_entity_utils import handle_transform_edit_mode

from engine.cue.entities.bt_static_mesh import BtStaticMesh
from engine.cue.rendering import cue_gizmos as gizmo 

import math

# a simple mesh that is part of the players view model

@dataclass(init=False, slots=True)
class SpsViewMesh:
    def __init__(self, en_data: dict) -> None:
        self.view_ease_power = en_data["easing_scalar"]

        self.track_trans = Transform(GameState.active_camera.cam_pos, -GameState.active_camera.cam_rot)

        self.view_space_trans = Transform(en_data["t_pos"], en_data["t_rot"], Vec3(en_data["t_scale"]))
        self.view_space_trans.set_parent(self.track_trans)

        self.mesh_renderer = ModelRenderer(en_data, self.view_space_trans)

        seq.next(self.tick)

    def tick(self) -> None:
        self.track_trans.set_pos_rot(self.track_trans._pos + ((GameState.active_camera.cam_pos - self.track_trans._pos) * min(self.view_ease_power * math.sqrt(GameState.delta_time), 1.)),
                                     self.track_trans._rot + ((-GameState.active_camera.cam_rot - self.track_trans._rot) * min(self.view_ease_power * math.sqrt(GameState.delta_time), 1.)))

        self.view_space_trans._update() # update internal matrix in case cam pos changed

        seq.next(self.tick)

    # == entity hooks ==

    @staticmethod
    def spawn(en_data: dict) -> 'SpsViewMesh':
        return SpsViewMesh(en_data)

    def despawn(self) -> None:
        self.mesh_renderer.hide() # hide until this class gets garbage collected

    @staticmethod
    def dev_tick(s: dict | None, dev_state: en.DevTickState, en_data: dict) -> dict:
        if s is None:
            # in editor BtStaticMesh is used for preview
            s = {"mesh": BtStaticMesh(en_data), "en_data": dict(en_data)}
        elif en_data != s["en_data"]:
            del s["mesh"]
            s["mesh"] = BtStaticMesh(en_data)
            s["en_data"] = dict(en_data)

        # handle trasnsform editing
        if dev_state.is_entity_selected:
            handle_transform_edit_mode(s, dev_state, en_data)

            # draw relative "camera" for editing
            min_p = -Vec3(.2, .2, .2)
            max_p =  Vec3(.2, .2, .2)
            line_col = Vec3(1., 1., .2)

            gizmo.draw_box(min_p, max_p, line_col)

            s["mesh"].mesh_renderer.show()
        else:
            s["mesh"].mesh_renderer.hide()

        return s

    view_ease_power: float
    track_trans: Transform

    view_space_trans: Transform
    mesh_renderer: ModelRenderer

def gen_def_data():
    return {
        "t_pos": Vec3(0.0, 0.0, 0.0),
        "t_rot": Vec3([0.0, 0.0, 0.0]),
        "t_scale": Vec3([1.0, 1.0, 1.0]),
        "easing_scalar": .45,
        "a_model_mesh": "models/icosph.npz",
        "a_model_vshader": "shaders/base_cam.vert",
        "a_model_fshader": "shaders/unlit.frag",
        "a_model_albedo": "textures/def_white.png",
        "a_model_transparent": False,
        "a_model_uniforms": {},
    }

en.create_entity_type("sps_view_mesh", SpsViewMesh.spawn, SpsViewMesh.despawn, SpsViewMesh.dev_tick, gen_def_data)