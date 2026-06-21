"""Output validation reports for exported alpha PNG assets."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from .exceptions import ProcessingError
from .models import ExportTarget, ProcessingOptions, ProcessResult

PNG_FORMAT = "png"


@dataclass(frozen=True)
class OutputValidationReport:
    """Detailed validation result for one exported PNG asset."""

    output_path: Path
    target: ExportTarget
    format_name: str
    mode: str
    width: int
    height: int
    file_size_bytes: int
    alpha_min: int
    alpha_max: int
    visible_percent: float
    bbox: tuple[int, int, int, int] | None
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def size_label(self) -> str:
        """Return a compact width/height label."""

        return f"{self.width}x{self.height}"

    @property
    def alpha_label(self) -> str:
        """Return a compact alpha-channel diagnostics label."""

        return f"alpha {self.alpha_min}-{self.alpha_max}, visible {self.visible_percent:.1f}%"


@dataclass(frozen=True)
class OutputValidationSpec:
    """Validation contract derived from the export target and processing options."""

    target: ExportTarget
    expected_format: str = PNG_FORMAT
    expected_size: tuple[int, int] | None = None
    require_background_removed: bool = True


def _expected_size(target: ExportTarget, options: ProcessingOptions) -> tuple[int, int] | None:
    if target == "resolume" and options.canvas_width and options.canvas_height:
        return (options.canvas_width, options.canvas_height)
    return None


def spec_from_options(
    options: ProcessingOptions,
    *,
    target: ExportTarget,
    require_background_removed: bool = True,
) -> OutputValidationSpec:
    """Build an output-validation contract from processing options."""

    return OutputValidationSpec(
        target=target,
        expected_format=options.output_format,
        expected_size=_expected_size(target, options),
        require_background_removed=require_background_removed,
    )


def _visible_alpha_percent(alpha: Image.Image) -> float:
    histogram = alpha.histogram()
    total_pixels = max(1, alpha.width * alpha.height)
    transparent_pixels = histogram[0] if histogram else 0
    visible_pixels = total_pixels - transparent_pixels
    return (visible_pixels / total_pixels) * 100.0


def _diagnostic_warnings(
    *,
    target: ExportTarget,
    alpha_min: int,
    alpha_max: int,
    visible_percent: float,
    bbox: tuple[int, int, int, int] | None,
    image_size: tuple[int, int],
) -> tuple[str, ...]:
    warnings: list[str] = []
    if alpha_max == 0:
        warnings.append("Alpha is fully transparent; the visible motif is empty.")
    if alpha_min == 255:
        warnings.append("Alpha is fully opaque; no transparent background is visible.")
    if 0 < visible_percent < 1.0:
        warnings.append("Visible motif is very small; check scale and placement before live use.")
    if target == "resolume" and bbox is not None:
        bbox_w = max(0, bbox[2] - bbox[0])
        bbox_h = max(0, bbox[3] - bbox[1])
        img_w, img_h = image_size
        if img_w > 0 and img_h > 0 and (bbox_w / img_w < 0.04 or bbox_h / img_h < 0.04):
            warnings.append("Visible alpha bounds are extremely thin for a Resolume canvas.")
    return tuple(warnings)


def validate_output_file(
    result: ProcessResult,
    options: ProcessingOptions,
    *,
    target: ExportTarget,
    require_background_removed: bool = True,
) -> OutputValidationReport:
    """Validate an exported alpha PNG and return a detailed report."""

    spec = spec_from_options(options, target=target, require_background_removed=require_background_removed)
    if spec.require_background_removed and (not options.remove_background or not result.background_removed):
        raise ProcessingError("Export must remove the background; refusing non-rembg output.")
    if spec.expected_format != PNG_FORMAT:
        raise ProcessingError(f"Export must be PNG, got: {spec.expected_format}")
    if result.output_path.suffix.lower() != ".png":
        raise ProcessingError(f"Export must write a .png file, got: {result.output_path.name}")
    if spec.expected_size and (result.width, result.height) != spec.expected_size:
        expected_w, expected_h = spec.expected_size
        raise ProcessingError(
            f"Resolume export must be {expected_w}x{expected_h}, got {result.width}x{result.height}."
        )

    try:
        file_size = result.output_path.stat().st_size
        with Image.open(result.output_path) as image:
            if image.format != "PNG":
                raise ProcessingError(f"Export wrote a non-PNG file: {image.format}")
            if spec.expected_size and image.size != spec.expected_size:
                raise ProcessingError(f"Saved PNG has wrong size: {image.size}")
            rgba = image.convert("RGBA")
            alpha = rgba.getchannel("A")
            alpha_min, alpha_max = alpha.getextrema()
            bbox = alpha.getbbox()
            visible_percent = _visible_alpha_percent(alpha)
            report = OutputValidationReport(
                output_path=result.output_path,
                target=target,
                format_name=image.format or "PNG",
                mode=image.mode,
                width=rgba.width,
                height=rgba.height,
                file_size_bytes=file_size,
                alpha_min=alpha_min,
                alpha_max=alpha_max,
                visible_percent=visible_percent,
                bbox=bbox,
                warnings=_diagnostic_warnings(
                    target=target,
                    alpha_min=alpha_min,
                    alpha_max=alpha_max,
                    visible_percent=visible_percent,
                    bbox=bbox,
                    image_size=rgba.size,
                ),
            )
    except ProcessingError:
        raise
    except Exception as exc:
        raise ProcessingError(
            f"Could not validate exported PNG: {result.output_path}. Original error: {exc}"
        ) from exc

    if report.alpha_max == 0:
        raise ProcessingError("Background removal produced a fully transparent image; refusing empty output.")
    if report.alpha_min == 255:
        raise ProcessingError(
            "Background removal produced a fully opaque PNG. "
            "Refusing output because no transparent background was detected."
        )
    return report
