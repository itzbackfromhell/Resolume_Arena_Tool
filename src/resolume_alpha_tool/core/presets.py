"""Preset loading and conversion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ProcessingOptions


def load_presets(path: Path) -> dict[str, dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Preset file must contain an object")
    return data


def options_from_preset(preset: dict[str, Any], base: ProcessingOptions | None = None) -> ProcessingOptions:
    source = base or ProcessingOptions()
    allowed = set(ProcessingOptions.__dataclass_fields__.keys())
    values = {key: getattr(source, key) for key in allowed}
    for key, value in preset.items():
        if key in allowed:
            values[key] = value
    return ProcessingOptions(**values)
