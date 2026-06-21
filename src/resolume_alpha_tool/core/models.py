"""Dataclasses shared by the focused export pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

ImageFormat = Literal["png"]
FitMode = Literal["none", "contain", "cover", "stretch"]
ExportTarget = Literal["resolume", "shirt_print"]


@dataclass(frozen=True)
class ProcessingOptions:
    """Options controlling one deterministic image-processing operation."""

    remove_background: bool = False
    rembg_model: str = "u2net"
    alpha_threshold: int = 8
    feather_radius: float = 0.8
    alpha_gamma: float = 1.0
    despill_strength: float = 0.35
    transparent_rgb_cleanup: bool = True
    trim_to_alpha: bool = False
    padding: int = 0
    fit_mode: FitMode = "none"
    canvas_width: int | None = None
    canvas_height: int | None = None
    output_format: ImageFormat = "png"
    overwrite: bool = False
    suffix: str = "_alpha"

    def normalized_suffix(self) -> str:
        suffix = self.suffix.strip()
        return suffix if suffix else "_alpha"


@dataclass(frozen=True)
class ProcessResult:
    """Result of one processed asset."""

    input_path: Path
    output_path: Path
    width: int
    height: int
    had_alpha: bool
    background_removed: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)
