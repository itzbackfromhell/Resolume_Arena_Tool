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


def ensure_dir(path: Path, *, create: bool = False) -> Path:
    path = path.expanduser().resolve()
    if not path.exists() and create:
        path.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        raise ValidationError(f"Directory does not exist: {path}")
    if not path.is_dir():
        raise ValidationError(f"Path is not a directory: {path}")
    return path


def iter_images(path: Path) -> list[Path]:
    directory = ensure_dir(path)
    return sorted(
        child
        for child in directory.iterdir()
        if child.is_file() and child.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    )
