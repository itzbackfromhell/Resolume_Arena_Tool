"""Single-image export service for Resolume and print targets."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .alpha_processor import process_file
from .exceptions import ProcessingError
from .models import ExportTarget, ProcessingOptions, ProcessResult
from .naming import build_output_path
from .validation import ensure_file

ProgressCallback = Callable[[str], None]
RESOLUME_CANVAS_SIZE = (1920, 1080)
RESOLUME_OUTPUT_FORMAT = "png"
RESOLUME_OUTPUT_SUFFIX = "_resolume"
SHIRT_PRINT_OUTPUT_SUFFIX = "_shirt_print"
DEFAULT_REMBG_MODEL = "u2net"
EXPORT_TARGETS: tuple[ExportTarget, ...] = ("resolume", "shirt_print")
CLI_TARGET_CHOICES = ("resolume", "shirt-print")


@dataclass(frozen=True)
class ExportJob:
    """One fixed alpha export request."""

    input_path: Path
    output_dir: Path
    target: ExportTarget = "resolume"
    model: str = DEFAULT_REMBG_MODEL


def normalize_export_target(value: str) -> ExportTarget:
    normalized = value.strip().lower().replace("-", "_")
    if normalized in EXPORT_TARGETS:
        return normalized  # type: ignore[return-value]
    raise ProcessingError(f"Unknown export target: {value}. Expected: resolume or shirt-print.")


def resolume_processing_options(model: str = DEFAULT_REMBG_MODEL) -> ProcessingOptions:
    """Return the fixed Resolume video/VJ export settings."""

    width, height = RESOLUME_CANVAS_SIZE
    return ProcessingOptions(
        remove_background=True,
        rembg_model=model,
        alpha_threshold=8,
        feather_radius=0.8,
        alpha_gamma=1.0,
        despill_strength=0.35,
        trim_to_alpha=False,
        padding=0,
        fit_mode="contain",
        canvas_width=width,
        canvas_height=height,
        output_format=RESOLUME_OUTPUT_FORMAT,
        suffix=RESOLUME_OUTPUT_SUFFIX,
        overwrite=False,
    )


def shirt_print_processing_options(model: str = DEFAULT_REMBG_MODEL) -> ProcessingOptions:
    """Return print-on-demand PNG settings with a tighter, cleaner transparent cutout."""

    return ProcessingOptions(
        remove_background=True,
        rembg_model=model,
        alpha_threshold=28,
        feather_radius=0.15,
        alpha_gamma=1.08,
        despill_strength=0.2,
        trim_to_alpha=True,
        padding=96,
        fit_mode="none",
        canvas_width=None,
        canvas_height=None,
        output_format=RESOLUME_OUTPUT_FORMAT,
        suffix=SHIRT_PRINT_OUTPUT_SUFFIX,
        overwrite=False,
    )


def processing_options_for_target(
    target: ExportTarget | str,
    model: str = DEFAULT_REMBG_MODEL,
) -> ProcessingOptions:
    export_target = normalize_export_target(str(target))
    if export_target == "shirt_print":
        return shirt_print_processing_options(model)
    return resolume_processing_options(model)


def build_alpha_output_path(
    input_path: Path,
    output_dir: Path,
    options: ProcessingOptions | None = None,
    *,
    target: ExportTarget | str = "resolume",
) -> Path:
    """Return the collision-safe output path for an alpha PNG export."""

    export_options = options or processing_options_for_target(target)
    return build_output_path(
        input_path,
        output_dir,
        suffix=export_options.normalized_suffix(),
        extension=export_options.output_format,
        overwrite=export_options.overwrite,
    )


def build_resolume_output_path(
    input_path: Path,
    output_dir: Path,
    options: ProcessingOptions | None = None,
) -> Path:
    """Return the collision-safe output path for a Resolume PNG export."""

    return build_alpha_output_path(input_path, output_dir, options, target="resolume")


def validate_alpha_output(
    result: ProcessResult,
    options: ProcessingOptions,
    *,
    target: ExportTarget,
) -> None:
    """Validate that the saved file is a real background-removed transparent PNG."""

    if not options.remove_background or not result.background_removed:
        raise ProcessingError("Export must remove the background; refusing non-rembg output.")
    if options.output_format != RESOLUME_OUTPUT_FORMAT:
        raise ProcessingError(f"Export must be PNG, got: {options.output_format}")
    if result.output_path.suffix.lower() != ".png":
        raise ProcessingError(f"Export must write a .png file, got: {result.output_path.name}")
    if target == "resolume" and (result.width, result.height) != RESOLUME_CANVAS_SIZE:
        raise ProcessingError(
            f"Resolume export must be {RESOLUME_CANVAS_SIZE[0]}x{RESOLUME_CANVAS_SIZE[1]}, "
            f"got {result.width}x{result.height}."
        )

    try:
        with Image.open(result.output_path) as image:
            if image.format != "PNG":
                raise ProcessingError(f"Export wrote a non-PNG file: {image.format}")
            if target == "resolume" and image.size != RESOLUME_CANVAS_SIZE:
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


def validate_resolume_output(result: ProcessResult, options: ProcessingOptions) -> None:
    """Validate that the saved file is a real alpha PNG for the fixed Resolume workflow."""

    validate_alpha_output(result, options, target="resolume")


def export_alpha_image(
    input_path: Path,
    output_dir: Path,
    *,
    target: ExportTarget | str = "resolume",
    model: str = DEFAULT_REMBG_MODEL,
    on_progress: ProgressCallback | None = None,
) -> ProcessResult:
    """Convert one image into a background-removed transparent PNG for the requested target."""

    export_target = normalize_export_target(str(target))
    source = ensure_file(input_path)
    options = processing_options_for_target(export_target, model)
    if not options.remove_background:
        raise ProcessingError("Export is not allowed to run with background removal disabled.")

    output_path = build_alpha_output_path(source, output_dir, options, target=export_target)
    if on_progress:
        label = "shirt/print PNG" if export_target == "shirt_print" else "Resolume PNG"
        on_progress(f"Removing background from {source.name} for {label}")
    result = process_file(source, output_path, options)
    try:
        validate_alpha_output(result, options, target=export_target)
    except ProcessingError:
        result.output_path.unlink(missing_ok=True)
        raise
    if on_progress:
        on_progress(f"Saved background-removed PNG: {result.output_path.name}")
    return result


def export_resolume_image(
    input_path: Path,
    output_dir: Path,
    *,
    model: str = DEFAULT_REMBG_MODEL,
    on_progress: ProgressCallback | None = None,
) -> ProcessResult:
    """Convert one image into a transparent 1920x1080 PNG for Resolume."""

    return export_alpha_image(input_path, output_dir, target="resolume", model=model, on_progress=on_progress)


def export_shirt_print_image(
    input_path: Path,
    output_dir: Path,
    *,
    model: str = DEFAULT_REMBG_MODEL,
    on_progress: ProgressCallback | None = None,
) -> ProcessResult:
    """Convert one image into a transparent PNG suitable for print-on-demand upload."""

    return export_alpha_image(input_path, output_dir, target="shirt_print", model=model, on_progress=on_progress)
