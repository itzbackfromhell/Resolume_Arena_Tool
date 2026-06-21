"""Input validation helpers."""

from __future__ import annotations

from pathlib import Path

from .exceptions import ValidationError

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def ensure_file(path: Path) -> Path:
    path = path.expanduser().resolve()
    if not path.exists():
        raise ValidationError(f"Input file does not exist: {path}")
    if not path.is_file():
        raise ValidationError(f"Input path is not a file: {path}")
    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValidationError(f"Unsupported image extension: {path.suffix}")
    return path
