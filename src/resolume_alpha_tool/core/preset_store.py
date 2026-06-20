"""User-preset helpers for the desktop GUI."""

from __future__ import annotations

from typing import Any

from .models import ProcessingOptions

CUSTOM_PRESET_NAME = "Custom"
PRESET_NAME_FORBIDDEN_CHARS = set('/\\:*?"<>|')
ALLOWED_PRESET_FIELDS = tuple(ProcessingOptions.__dataclass_fields__.keys())


def clean_preset_name(value: str) -> str:
    """Return a safe display name for a user preset."""

    name = " ".join(value.strip().split())
    if not name:
        raise ValueError("Preset name cannot be empty.")
    if name.lower() == CUSTOM_PRESET_NAME.lower():
        raise ValueError(f"'{CUSTOM_PRESET_NAME}' is reserved.")
    if any(char in PRESET_NAME_FORBIDDEN_CHARS for char in name):
        raise ValueError("Preset name contains a Windows path character.")
    return name


def normalize_preset(raw: dict[str, Any]) -> dict[str, Any]:
    """Keep only ProcessingOptions fields from a raw preset dict."""

    return {key: raw[key] for key in ALLOWED_PRESET_FIELDS if key in raw}


def normalize_presets(raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Normalize a mapping of preset names to preset values."""

    normalized: dict[str, dict[str, Any]] = {}
    for name, preset in raw.items():
        if isinstance(name, str) and isinstance(preset, dict):
            cleaned = clean_preset_name(name)
            values = normalize_preset(preset)
            if values:
                normalized[cleaned] = values
    return normalized


def merge_presets(
    default_presets: dict[str, dict[str, Any]], user_presets: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Merge defaults with user presets; user presets may shadow defaults."""

    merged = dict(default_presets)
    merged.update(user_presets)
    return merged


def preset_from_options(options: ProcessingOptions) -> dict[str, Any]:
    """Serialize current processing options into a user-preset dict."""

    values: dict[str, Any] = {}
    for key in ALLOWED_PRESET_FIELDS:
        value = getattr(options, key)
        if value is not None:
            values[key] = value
    return values
