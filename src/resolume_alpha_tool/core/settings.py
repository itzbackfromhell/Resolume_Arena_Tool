"""Application settings service shared by UI and future workflows."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

APP_DIR_NAME = "AlphaPngExporter"
LEGACY_APP_DIR_NAME = "ResolumeAlphaDropper"
CONFIG_ENV_VAR = "ALPHA_PNG_EXPORTER_CONFIG_DIR"
LEGACY_CONFIG_ENV_VAR = "RESOLUME_ALPHA_DROPPER_CONFIG_DIR"
SETTINGS_FILE_NAME = "settings.json"
USER_PRESETS_FILE_NAME = "user_presets.json"

EXPORT_TARGETS = frozenset({"resolume", "shirt_print"})
RESOLUME_PRESETS = frozenset({"1080p", "4k", "square_1080", "square-1080"})
FIT_MODES = frozenset({"contain", "cover", "stretch"})
PREVIEW_MODES = frozenset({"checker", "black", "white", "alpha"})
EDGE_PROFILES = frozenset({"normal", "soft", "tight", "grow"})


@dataclass(frozen=True)
class AppSettings:
    """Typed, sanitized app settings used by the desktop workflow."""

    input_path: str = ""
    batch_dir: str = ""
    output_dir: str = ""
    export_target: str = "resolume"
    resolume_preset: str = "1080p"
    fit_mode: str = "contain"
    preview_mode: str = "checker"
    edge_profile: str = "normal"
    shirt_padding: int = 96
    batch_both_targets: bool = False
    batch_recursive: bool = False
    open_after_export: bool = False
    window_geometry: str = ""

    def to_json_object(self) -> dict[str, str | int | bool]:
        """Return a JSON-object-compatible representation."""

        return asdict(self)


def _pick_config_dir(root: Path) -> Path:
    current = root / APP_DIR_NAME
    legacy = root / LEGACY_APP_DIR_NAME
    if not current.exists() and legacy.exists():
        return legacy
    return current


def config_dir() -> Path:
    """Return the active per-user configuration directory."""

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
    """Load one JSON object, returning an empty object for missing or invalid data."""

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_json_object(path: Path, data: dict[str, Any]) -> None:
    """Persist one JSON object with stable formatting."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _string_value(raw: dict[str, Any], key: str, default: str = "") -> str:
    value = raw.get(key, default)
    if isinstance(value, str):
        return value
    if value is None:
        return default
    return str(value)


def _choice_value(raw: dict[str, Any], key: str, choices: frozenset[str], default: str) -> str:
    value = _string_value(raw, key, default).strip().lower().replace("-", "_")
    normalized_choices = {choice.replace("-", "_") for choice in choices}
    if value in normalized_choices:
        return value
    return default


def _bool_value(raw: dict[str, Any], key: str, default: bool = False) -> bool:
    value = raw.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "yes", "true", "on"}
    return bool(value)


def _int_value(raw: dict[str, Any], key: str, default: int, *, minimum: int = 0, maximum: int | None = None) -> int:
    value = raw.get(key, default)
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    number = max(minimum, number)
    if maximum is not None:
        number = min(maximum, number)
    return number


def sanitize_settings(raw: dict[str, Any]) -> AppSettings:
    """Normalize arbitrary JSON data into safe application settings."""

    return AppSettings(
        input_path=_string_value(raw, "input_path"),
        batch_dir=_string_value(raw, "batch_dir"),
        output_dir=_string_value(raw, "output_dir"),
        export_target=_choice_value(raw, "export_target", EXPORT_TARGETS, "resolume"),
        resolume_preset=_choice_value(raw, "resolume_preset", RESOLUME_PRESETS, "1080p"),
        fit_mode=_choice_value(raw, "fit_mode", FIT_MODES, "contain"),
        preview_mode=_choice_value(raw, "preview_mode", PREVIEW_MODES, "checker"),
        edge_profile=_choice_value(raw, "edge_profile", EDGE_PROFILES, "normal"),
        shirt_padding=_int_value(raw, "shirt_padding", 96, minimum=0, maximum=320),
        batch_both_targets=_bool_value(raw, "batch_both_targets"),
        batch_recursive=_bool_value(raw, "batch_recursive"),
        open_after_export=_bool_value(raw, "open_after_export"),
        window_geometry=_string_value(raw, "window_geometry"),
    )


def load_app_settings(path: Path | None = None) -> AppSettings:
    """Load typed settings from disk."""

    return sanitize_settings(load_json_object(path or settings_path()))


def save_app_settings(settings: AppSettings, path: Path | None = None) -> None:
    """Persist typed settings to disk."""

    save_json_object(path or settings_path(), settings.to_json_object())


def app_settings_from_json_object(raw: dict[str, Any]) -> AppSettings:
    """Public alias for callers migrating from raw dictionaries."""

    return sanitize_settings(raw)


def app_settings_keys() -> tuple[str, ...]:
    """Return the stable settings key order for UI migration tests."""

    return tuple(field.name for field in fields(AppSettings))
