"""Resource and writable-path helpers for source and frozen builds."""

from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "ResolumeAlphaDropper"


def is_frozen() -> bool:
    """Return True when running from a PyInstaller executable."""

    return bool(getattr(sys, "frozen", False))


def executable_dir() -> Path:
    """Return the executable folder for frozen builds, otherwise the repo root."""

    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def bundled_root() -> Path:
    """Return the directory where bundled read-only resources live."""

    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()  # type: ignore[attr-defined]
    return executable_dir()


def bundled_resource_path(*parts: str) -> Path:
    """Return a resource path valid in source and PyInstaller modes."""

    return bundled_root().joinpath(*parts)


def portable_root() -> Path:
    """Return the writable app folder beside the executable/source checkout."""

    return executable_dir()


def portable_output_dir() -> Path:
    return portable_root() / "output"


def portable_log_dir() -> Path:
    return portable_root() / "logs"


def default_preset_path() -> Path:
    """Return the bundled default preset JSON path."""

    portable_preset = portable_root() / "presets" / "defaults.json"
    if portable_preset.exists():
        return portable_preset
    return bundled_resource_path("presets", "defaults.json")


def ensure_portable_dirs() -> None:
    """Create writable folders expected by portable releases."""

    portable_output_dir().mkdir(parents=True, exist_ok=True)
    portable_log_dir().mkdir(parents=True, exist_ok=True)
