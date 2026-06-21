"""Persistent GUI settings helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

APP_DIR_NAME = "AlphaPngExporter"
LEGACY_APP_DIR_NAME = "ResolumeAlphaDropper"
CONFIG_ENV_VAR = "ALPHA_PNG_EXPORTER_CONFIG_DIR"
LEGACY_CONFIG_ENV_VAR = "RESOLUME_ALPHA_DROPPER_CONFIG_DIR"
SETTINGS_FILE_NAME = "settings.json"
USER_PRESETS_FILE_NAME = "user_presets.json"


def _pick_config_dir(root: Path) -> Path:
    current = root / APP_DIR_NAME
    legacy = root / LEGACY_APP_DIR_NAME
    if not current.exists() and legacy.exists():
        return legacy
    return current


def config_dir() -> Path:
    override = os.environ.get(CONFIG_ENV_VAR) or os.environ.get(LEGACY_CONFIG_ENV_VAR)
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return _pick_config_dir(Path(appdata))
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return _pick_config_dir(Path(xdg_config_home))
    return _pick_config_dir(Path.home() / ".config")


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
