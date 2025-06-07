import json
import logging
from datetime import datetime

from rui.common import config

_path = config.get("persistence.path")
logger = logging.getLogger(__name__)


def get(key: str, path: str = _path):
    key = str(key)

    try:
        with open(path, "r") as data_file:
            data = json.load(data_file)
    except FileNotFoundError:
        with open(path, "w") as data_file:
            json.dump({}, data_file)

        return get(key, path)
    except json.JSONDecodeError:
        with open(path, "w") as data_file:
            json.dump({}, data_file)

        return get(key, path)

    if not data.get(key):
        return {}

    return data[key]


def set(key: str, value: dict, path: str = _path, indent: int | None = 2):
    key = str(key)

    with open(path, "r") as data_file:
        data = json.load(data_file)

    now = datetime.now()
    value["_last_update"] = now.strftime("%Y-%m-%d %H:%M:%S")
    data[key] = value

    with open(path, "w") as data_file:
        json.dump(data, data_file, indent=indent)
