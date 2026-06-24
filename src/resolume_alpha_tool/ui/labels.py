"""Stable UI labels and option keys for the desktop app."""

from __future__ import annotations

from resolume_alpha_tool.core.models import ExportTarget

IMAGE_FILETYPES = [("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("All", "*.*")]
PREVIEW_SIZE = (420, 300)
TARGET_LABELS: dict[ExportTarget, str] = {
    "resolume": "Resolume PNG",
    "shirt_print": "Shirt/Print PNG",
}
RESOLUME_PRESET_LABELS = {
    "1080p": "Resolume 1080p",
    "4k": "Resolume 4K",
    "square_1080": "Square 1080",
}
PREVIEW_MODE_LABELS = {
    "checker": "Checker",
    "black": "Black",
    "white": "White",
    "alpha": "Alpha matte",
    "bounds": "Bounds",
}
EDGE_PROFILE_LABELS = {
    "normal": "Normal",
    "soft": "Soft feather",
    "tight": "Tight cut",
    "grow": "Grow edge",
}


def target_label(target: ExportTarget) -> str:
    """Return a human-readable export target label."""

    return TARGET_LABELS[target]


def preview_mode_keys() -> tuple[str, ...]:
    """Return preview mode keys in stable UI order."""

    return tuple(PREVIEW_MODE_LABELS)
