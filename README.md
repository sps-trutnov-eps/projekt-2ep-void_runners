# Void Runners

A simple FPS set in an unknown location.

> [!note]
> On Windows, python 3.11.9 is recomended otherwise windows C++ build tools will *need* to be available to install dependencies

To run first update the engine submodule and install requirements
```sh
git submodule update --init
python -m pip install -r source/engine/requirements.txt
```

Then to run start with `main.py`
```sh
python source/main.py
```

### Map Editor

To use the engines editor first download its extra requirements
```sh
python -m pip install -r source/engine/requirements.txt -r source/engine/requirements_editor.txt
```

Then you can start the editor
```sh
python source/editor.py
```
