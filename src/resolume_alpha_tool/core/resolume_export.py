"""Single-image Resolume export service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .alpha_processor import process_file
from .models import ProcessingOptions, ProcessResult
from .naming import build_output_path
from .validation import ensure_file

ProgressCallback = Callable[[str], None]
RESOLUME_CANVAS_SIZE = (1920, 1080)
RESOLUME_OUTPUT_FORMAT = "png"
RESOLUME_OUTPUT_SUFFIX = "_resolume"
DEFAULT_REMBG_MODEL = "u2net"


@dataclass(frozen=True)
class ExportJob:
    """One fixed Resolume image export request."""

    input_path: Path
    output_dir: Path
    model: str = DEFAULT_REMBG_MODEL


def resolume_processing_options(model: str = DEFAULT_REMBG_MODEL) -> ProcessingOptions:
    """Return the only supported GUI/CLI export settings."""

    width, height = RESOLUME_CANVAS_SIZE
    return ProcessingOptions(
        remove_background=True,
        rembg_model=model,
        alpha_threshold=8,
        feather_radius=0.8,
        alpha_gamma=1.0,
        despill_strength=0.35,
        fit_mode="contain",
        canvas_width=width,
        canvas_height=height,
        output_format=RESOLUME_OUTPUT_FORMAT,
        suffix=RESOLUME_OUTPUT_SUFFIX,
        overwrite=False,
    )


def build_resolume_output_path(
    input_path: Path,
    output_dir: Path,
    options: ProcessingOptions | None = None,
) -> Path:
    """Return the collision-safe output path for a Resolume PNG export."""

    export_options = options or resolume_processing_options()
    return build_output_path(
        input_path,
        output_dir,
        suffix=export_options.normalized_suffix(),
        extension=export_options.output_format,
        overwrite=export_options.overwrite,
    )


def export_resolume_image(
    input_path: Path,
    output_dir: Path,
    *,
    model: str = DEFAULT_REMBG_MODEL,
    on_progress: ProgressCallback | None = None,
) -> ProcessResult:
    """Convert one image into a transparent 1920x1080 PNG for Resolume."""

    source = ensure_file(input_path)
    options = resolume_processing_options(model)
    output_path = build_resolume_output_path(source, output_dir, options)
    if on_progress:
        on_progress(f"Processing {source.name}")
    result = process_file(source, output_path, options)
    if on_progress:
        on_progress(f"Saved {result.output_path.name}")
    return result
