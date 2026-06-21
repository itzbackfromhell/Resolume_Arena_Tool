"""Path and image-input helpers for the GUI."""

from __future__ import annotations

from pathlib import Path

from .validation import SUPPORTED_IMAGE_EXTENSIONS

SUPPORTED_IMAGE_SUFFIXES = frozenset(SUPPORTED_IMAGE_EXTENSIONS)


def clean_path_text(value: str) -> str:
    """Normalize text pasted from Windows Explorer, terminals, or quoted command lines."""

    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        text = text[1:-1].strip()
    return text


def is_supported_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
