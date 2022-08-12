import json
import os

from .history import History

application_name = "RSAtrace3D"
version = 1
revision = 3


def version_string():
    return f"{version}.{revision}"


def parse_version_string(version_string):
    return [int(i) for i in version_string.split(sep=".")]


config_dir = os.path.dirname(__file__)
config_file = os.path.join(config_dir, "config.json")

params = {}


def save(**params):
    with open(config_file, "w") as f:
        json.dump(params, f, indent=3)


def load():
    if not os.path.isfile(config_file):
        return {}

    with open(config_file, "r") as f:
        config_dict = json.load(f)

    return config_dict
