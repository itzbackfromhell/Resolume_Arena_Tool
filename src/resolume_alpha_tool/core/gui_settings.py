"""Persistent GUI settings helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

APP_DIR_NAME = "ResolumeAlphaDropper"
SETTINGS_FILE_NAME = "settings.json"
USER_PRESETS_FILE_NAME = "user_presets.json"


def config_dir() -> Path:
    override = os.environ.get("RESOLUME_ALPHA_DROPPER_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / APP_DIR_NAME
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / APP_DIR_NAME
    return Path.home() / ".config" / APP_DIR_NAME


def settings_path() -> Path:
    return config_dir() / SETTINGS_FILE_NAME


def user_presets_path() -> Path:
    return config_dir() / USER_PRESETS_FILE_NAME


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_json_object(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
