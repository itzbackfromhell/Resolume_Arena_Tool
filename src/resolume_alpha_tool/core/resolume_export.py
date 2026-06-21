"""Single-image Resolume export service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .alpha_processor import process_file
from .exceptions import ProcessingError
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


def validate_resolume_output(result: ProcessResult, options: ProcessingOptions) -> None:
    """Validate that the saved file is a real alpha PNG for the fixed Resolume workflow."""

    if not options.remove_background or not result.background_removed:
        raise ProcessingError("Resolume export must remove the background; refusing non-rembg output.")
    if options.output_format != RESOLUME_OUTPUT_FORMAT:
        raise ProcessingError(f"Resolume export must be PNG, got: {options.output_format}")
    if (result.width, result.height) != RESOLUME_CANVAS_SIZE:
        raise ProcessingError(
            f"Resolume export must be {RESOLUME_CANVAS_SIZE[0]}x{RESOLUME_CANVAS_SIZE[1]}, "
            f"got {result.width}x{result.height}."
        )
    if result.output_path.suffix.lower() != ".png":
        raise ProcessingError(f"Resolume export must write a .png file, got: {result.output_path.name}")

    try:
        with Image.open(result.output_path) as image:
            if image.format != "PNG":
                raise ProcessingError(f"Resolume export wrote a non-PNG file: {image.format}")
            if image.size != RESOLUME_CANVAS_SIZE:
                raise ProcessingError(f"Saved PNG has wrong size: {image.size}")
            rgba = image.convert("RGBA")
            alpha_min, alpha_max = rgba.getchannel("A").getextrema()
    except ProcessingError:
        raise
    except Exception as exc:
        raise ProcessingError(f"Could not validate exported PNG: {result.output_path}. Original error: {exc}") from exc

    if alpha_max == 0:
        raise ProcessingError("Background removal produced a fully transparent image; refusing empty output.")
    if alpha_min == 255:
        raise ProcessingError(
            "Background removal produced a fully opaque PNG. "
            "Refusing output because no transparent background was detected."
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
    if not options.remove_background:
        raise ProcessingError("Resolume export is not allowed to run with background removal disabled.")

    output_path = build_resolume_output_path(source, output_dir, options)
    if on_progress:
        on_progress(f"Removing background from {source.name}")
    result = process_file(source, output_path, options)
    try:
        validate_resolume_output(result, options)
    except ProcessingError:
        result.output_path.unlink(missing_ok=True)
        raise
    if on_progress:
        on_progress(f"Saved background-removed Resolume PNG: {result.output_path.name}")
    return result
