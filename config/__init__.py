import json
import os
from typing import Final

application_name = "RSAtrace3D"
version = 1
revision = 8

ALWAYS_YES = False
COLOR_ROOT_DEFAULT: Final[str] = "#00aa00"
COLOR_SELECTED_ROOT_DEFAULT: Final[str] = "#ffff00"
COLOR_ROOT = COLOR_ROOT_DEFAULT
COLOR_SELECTED_ROOT = COLOR_SELECTED_ROOT_DEFAULT

PROJECTION_INTENSITY = 1.0


def version_string():
    return f"{version}.{revision}"


def parse_version_string(version_string):
    return [int(i) for i in version_string.split(sep=".")]


config_dir = os.path.dirname(__file__)
config_file = os.path.join(config_dir, "config.json")

params = {}


def save(**params):
    params.update(
        {
            "root color": COLOR_ROOT,
            "selected root color": COLOR_SELECTED_ROOT,
            "projection intensity": PROJECTION_INTENSITY,
        }
    )
    with open(config_file, "w") as f:
        json.dump(params, f, indent=3)


def load():
    if not os.path.isfile(config_file):
        return {}

    with open(config_file, "r") as f:
        config_dict = json.load(f)

    global COLOR_ROOT, COLOR_SELECTED_ROOT, PROJECTION_INTENSITY

    COLOR_ROOT = config_dict.get("root color", COLOR_ROOT_DEFAULT)
    COLOR_SELECTED_ROOT = config_dict.get(
        "selected root color", COLOR_SELECTED_ROOT_DEFAULT
    )
    PROJECTION_INTENSITY = config_dict.get("projection intensity", 1.0)

    return config_dict


def reset_root_color():
    global COLOR_ROOT, COLOR_SELECTED_ROOT
    COLOR_ROOT = COLOR_ROOT_DEFAULT
    COLOR_SELECTED_ROOT = COLOR_SELECTED_ROOT_DEFAULT
