"""Dataclasses shared across CLI, GUI, and core services."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

ImageFormat = Literal["png", "webp"]
FitMode = Literal["none", "contain", "cover", "stretch"]


@dataclass(frozen=True)
class ProcessingOptions:
    """Options controlling a single image-processing operation."""

    remove_background: bool = False
    rembg_model: str = "u2net"
    alpha_threshold: int = 8
    feather_radius: float = 0.8
    alpha_gamma: float = 1.0
    despill_strength: float = 0.35
    transparent_rgb_cleanup: bool = True
    fit_mode: FitMode = "none"
    canvas_width: int | None = None
    canvas_height: int | None = None
    output_format: ImageFormat = "png"
    webp_quality: int = 95
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


@dataclass(frozen=True)
class BatchSummary:
    """Summary for a batch run."""

    processed: int
    failed: int
    skipped: int
    results: tuple[ProcessResult, ...]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class ResolumeConfig:
    """Local Resolume webserver configuration."""

    host: str = "127.0.0.1"
    port: int = 8080
    timeout_seconds: float = 2.0

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"
