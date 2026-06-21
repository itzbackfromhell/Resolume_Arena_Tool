"""Single-image export service for Resolume and print targets."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from PIL import Image

from .alpha_processor import process_file
from .exceptions import ProcessingError
from .models import ExportTarget, FitMode, ProcessingOptions, ProcessResult
from .naming import build_output_path
from .validation import ensure_file

ProgressCallback = Callable[[str], None]
RESOLUME_CANVAS_SIZE = (1920, 1080)
RESOLUME_4K_CANVAS_SIZE = (3840, 2160)
RESOLUME_OUTPUT_FORMAT = "png"
RESOLUME_OUTPUT_SUFFIX = "_resolume"
SHIRT_PRINT_OUTPUT_SUFFIX = "_shirt_print"
DEFAULT_REMBG_MODEL = "u2net"
EXPORT_TARGETS: tuple[ExportTarget, ...] = ("resolume", "shirt_print")
CLI_TARGET_CHOICES = ("resolume", "shirt-print")
RESOLUME_PRESETS: dict[str, tuple[int, int]] = {
    "1080p": RESOLUME_CANVAS_SIZE,
    "4k": RESOLUME_4K_CANVAS_SIZE,
    "square_1080": (1080, 1080),
}
EDGE_CLEANUP_PROFILES = ("normal", "soft", "tight", "grow")


@dataclass(frozen=True)
class ExportJob:
    """One fixed alpha export request."""

    input_path: Path
    output_dir: Path
    target: ExportTarget = "resolume"
    model: str = DEFAULT_REMBG_MODEL
    options: ProcessingOptions | None = None


def normalize_export_target(value: str) -> ExportTarget:
    normalized = value.strip().lower().replace("-", "_")
    if normalized in EXPORT_TARGETS:
        return normalized  # type: ignore[return-value]
    raise ProcessingError(f"Unknown export target: {value}. Expected: resolume or shirt-print.")


def normalize_resolume_preset(value: str) -> tuple[int, int]:
    """Return a known Resolume canvas size from a stable preset key."""

    key = value.strip().lower().replace("-", "_")
    if key in RESOLUME_PRESETS:
        return RESOLUME_PRESETS[key]
    raise ProcessingError(f"Unknown Resolume preset: {value}.")


def _edge_profile_values(profile: str) -> tuple[int, int, float]:
    normalized = profile.strip().lower().replace("-", "_")
    if normalized == "soft":
        return (0, 0, 1.4)
    if normalized == "tight":
        return (1, 0, 0.35)
    if normalized == "grow":
        return (0, 1, 0.45)
    if normalized == "normal":
        return (0, 0, 0.8)
    raise ProcessingError(f"Unknown edge cleanup profile: {profile}.")


def with_edge_cleanup_profile(options: ProcessingOptions, profile: str) -> ProcessingOptions:
    """Return options with a small safe alpha cleanup profile applied."""

    erode, dilate, feather = _edge_profile_values(profile)
    return replace(options, alpha_erode=erode, alpha_dilate=dilate, feather_radius=feather)


def resolume_processing_options(
    model: str = DEFAULT_REMBG_MODEL,
    *,
    canvas_size: tuple[int, int] = RESOLUME_CANVAS_SIZE,
    fit_mode: FitMode = "contain",
    edge_profile: str = "normal",
) -> ProcessingOptions:
    """Return Resolume video/VJ export settings."""

    width, height = canvas_size
    options = ProcessingOptions(
        remove_background=True,
        rembg_model=model,
        alpha_threshold=8,
        feather_radius=0.8,
        alpha_gamma=1.0,
        despill_strength=0.35,
        trim_to_alpha=False,
        padding=0,
        fit_mode=fit_mode,
        canvas_width=width,
        canvas_height=height,
        output_format=RESOLUME_OUTPUT_FORMAT,
        suffix=RESOLUME_OUTPUT_SUFFIX,
        overwrite=False,
    )
    return with_edge_cleanup_profile(options, edge_profile)


def shirt_print_processing_options(
    model: str = DEFAULT_REMBG_MODEL,
    *,
    padding: int = 96,
    edge_profile: str = "tight",
) -> ProcessingOptions:
    """Return print-on-demand PNG settings with a tighter, cleaner transparent cutout."""

    options = ProcessingOptions(
        remove_background=True,
        rembg_model=model,
        alpha_threshold=28,
        feather_radius=0.15,
        alpha_gamma=1.08,
        despill_strength=0.2,
        trim_to_alpha=True,
        padding=max(0, int(padding)),
        fit_mode="none",
        canvas_width=None,
        canvas_height=None,
        output_format=RESOLUME_OUTPUT_FORMAT,
        suffix=SHIRT_PRINT_OUTPUT_SUFFIX,
        overwrite=False,
    )
    return with_edge_cleanup_profile(options, edge_profile)


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
    if target == "resolume" and options.canvas_width and options.canvas_height:
        expected_size = (options.canvas_width, options.canvas_height)
        if (result.width, result.height) != expected_size:
            raise ProcessingError(
                f"Resolume export must be {expected_size[0]}x{expected_size[1]}, "
                f"got {result.width}x{result.height}."
            )

    try:
        with Image.open(result.output_path) as image:
            if image.format != "PNG":
                raise ProcessingError(f"Export wrote a non-PNG file: {image.format}")
            if target == "resolume" and options.canvas_width and options.canvas_height:
                expected_size = (options.canvas_width, options.canvas_height)
                if image.size != expected_size:
                    raise ProcessingError(f"Saved PNG has wrong size: {image.size}")
            rgba = image.convert("RGBA")
            alpha_min, alpha_max = rgba.getchannel("A").getextrema()
    except ProcessingError:
        raise
    except Exception as exc:
        raise ProcessingError(
            f"Could not validate exported PNG: {result.output_path}. Original error: {exc}"
        ) from exc

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
    options: ProcessingOptions | None = None,
    on_progress: ProgressCallback | None = None,
) -> ProcessResult:
    """Convert one image into a background-removed transparent PNG for the requested target."""

    export_target = normalize_export_target(str(target))
    source = ensure_file(input_path)
    export_options = options or processing_options_for_target(export_target, model)
    if not export_options.remove_background:
        raise ProcessingError("Export is not allowed to run with background removal disabled.")

    output_path = build_alpha_output_path(source, output_dir, export_options, target=export_target)
    if on_progress:
        label = "shirt/print PNG" if export_target == "shirt_print" else "Resolume PNG"
        on_progress(f"Removing background from {source.name} for {label}")
    result = process_file(source, output_path, export_options)
    try:
        validate_alpha_output(result, export_options, target=export_target)
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
