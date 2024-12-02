import os, json, copy

from engine.cue.cue_map import load_en_param_types
from engine.cue.cue_state import GameState

# a tiny entity prefab api engine extesion which is not part of the engine due to lack of polish

prefab_cache: dict[str, dict] = {}

def load_prefab(prefab_name: str, path: str) -> list:
    # load and cache
    
    p = prefab_cache.get(path, None)
    
    if p is None:
        with open(os.path.join(GameState.asset_manager.asset_dir, path), 'r') as f:
            p = json.load(f)
        prefab_cache[path] = p
    
    # copy and deserialize

    lp = []

    for en_name, data in p.items():
        en_type, en_data = data
        en_name = en_name.replace("[prefab_name]", prefab_name)
        
        lp.append((en_name, en_type, load_en_param_types(en_data)))
    
    return lp

def spawn_prefab(prefab: list) -> None:
    for en_name, en_type, en_data in prefab:
        GameState.entity_storage.spawn(en_type, en_name, load_en_param_types(en_data))

def spawn_prefab_from_file(prefab_name: str, path: str) -> None:
    spawn_prefab(load_prefab(prefab_name, path))