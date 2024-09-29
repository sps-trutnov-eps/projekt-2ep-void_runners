# == pre-imports ==

import OpenGL
OpenGL.ERROR_CHECKING = True
OpenGL.ERROR_LOGGING = True

# == import engine ==

try: import engine.cue.editor.on_cue as on_cue
except ImportError: 
    print("[\x1b[1m\x1b[31merror\x1b[0m] There was a problem importing the On-Cue Editor, make sure you pip installed the requirements.txt *and* requirements_editor.txt and did a `git submodule update --init`")
    raise

on_cue.start_editor()