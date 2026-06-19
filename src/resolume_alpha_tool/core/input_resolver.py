"""Path and image-input helpers for CLI/GUI workflows."""

from __future__ import annotations

from pathlib import Path

SUPPORTED_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"})


def clean_path_text(value: str) -> str:
    """Normalize text pasted from Windows Explorer, terminals, or quoted command lines."""

    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        text = text[1:-1].strip()
    return text


def is_supported_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES


def resolve_preview_source(path: Path) -> Path | None:
    """Return the image file to preview for either a file or folder input."""

    path = Path(clean_path_text(str(path))).expanduser()
    if is_supported_image(path):
        return path
    if path.is_dir():
        for candidate in sorted(path.rglob("*")):
            if is_supported_image(candidate):
                return candidate
    return None
