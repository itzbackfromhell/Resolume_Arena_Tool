"""Persistent GUI settings helpers.

This module is kept as the compatibility import surface for the current Tk app.
The first-class settings implementation lives in ``core.settings``.
"""

from __future__ import annotations

from .settings import (
    APP_DIR_NAME,
    CONFIG_ENV_VAR,
    LEGACY_APP_DIR_NAME,
    LEGACY_CONFIG_ENV_VAR,
    SETTINGS_FILE_NAME,
    USER_PRESETS_FILE_NAME,
    _pick_config_dir,
    config_dir,
    load_json_object,
    save_json_object,
    settings_path,
    user_presets_path,
)

__all__ = [
    "APP_DIR_NAME",
    "CONFIG_ENV_VAR",
    "LEGACY_APP_DIR_NAME",
    "LEGACY_CONFIG_ENV_VAR",
    "SETTINGS_FILE_NAME",
    "USER_PRESETS_FILE_NAME",
    "_pick_config_dir",
    "config_dir",
    "load_json_object",
    "save_json_object",
    "settings_path",
    "user_presets_path",
]
