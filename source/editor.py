# == pre-imports ==

import OpenGL, os
OpenGL.ERROR_CHECKING = True
OpenGL.ERROR_LOGGING = True

OpenGL.ERROR_ON_COPY = False

import sys, subprocess
def test_play(map_path: str):
    print()
    subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), "main.py"), "--bmap", map_path])

# == import engine ==

try: import engine.cue.editor.on_cue as on_cue
except ImportError: 
    print("[\x1b[1m\x1b[31merror\x1b[0m] There was a problem importing the On-Cue Editor, make sure you pip installed the requirements.txt *and* requirements_editor.txt and did a `git submodule update --init`")
    raise

# == import game entities ==
import entity.sps_player_spawn
import entity.sps_static_cam
import entity.sps_dev_text
import entity.sps_view_mesh
import entity.sps_hitbox_ai
import entity.sps_hurt_trigger

on_cue.EDITOR_ASSET_DIR = os.path.join(os.path.dirname(__file__), "../assets")
on_cue.EDITOR_TEST_PLAY_CALLBACK = test_play
on_cue.start_editor()