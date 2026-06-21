"""Alpha-channel diagnostics for previews and export warnings."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class AlphaDiagnostics:
    """Small, UI-friendly summary of one image's visible alpha content."""

    width: int
    height: int
    has_alpha: bool
    alpha_min: int
    alpha_max: int
    visible_percent: float
    bbox: tuple[int, int, int, int] | None
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def size_label(self) -> str:
        return f"{self.width}x{self.height}"

    @property
    def alpha_label(self) -> str:
        if not self.has_alpha:
            return "no alpha channel"
        return f"alpha {self.alpha_min}-{self.alpha_max}, visible {self.visible_percent:.1f}%"


def _alpha_warnings(
    *,
    has_alpha: bool,
    alpha_min: int,
    alpha_max: int,
    visible_percent: float,
    bbox: tuple[int, int, int, int] | None,
    image_size: tuple[int, int],
) -> tuple[str, ...]:
    warnings: list[str] = []
    if not has_alpha:
        warnings.append("No alpha channel yet; export will create one with rembg.")
    if alpha_max == 0:
        warnings.append("Alpha is fully transparent; the visible motif is empty.")
    if has_alpha and alpha_min == 255:
        warnings.append("Alpha is fully opaque; no transparent background is visible yet.")
    if 0 < visible_percent < 1.0:
        warnings.append("Visible motif is very small; check scaling before using this live.")
    if bbox is not None:
        bbox_w = max(0, bbox[2] - bbox[0])
        bbox_h = max(0, bbox[3] - bbox[1])
        img_w, img_h = image_size
        if img_w > 0 and img_h > 0 and (bbox_w / img_w < 0.08 or bbox_h / img_h < 0.08):
            warnings.append("Alpha bounds are extremely thin; result may look tiny in Resolume.")
    return tuple(warnings)


def _visible_alpha_percent(alpha: Image.Image) -> float:
    """Return visible alpha coverage using Pillow's C-backed histogram path."""

    histogram = alpha.histogram()
    total_pixels = max(1, alpha.width * alpha.height)
    transparent_pixels = histogram[0] if histogram else 0
    visible_pixels = total_pixels - transparent_pixels
    return (visible_pixels / total_pixels) * 100.0


def analyze_alpha_image_object(image: Image.Image) -> AlphaDiagnostics:
    """Return alpha diagnostics for an already opened image."""

    rgba = image.convert("RGBA")
    has_alpha = "A" in image.getbands()
    alpha = rgba.getchannel("A")
    alpha_min, alpha_max = alpha.getextrema()
    bbox = alpha.getbbox()
    visible_percent = _visible_alpha_percent(alpha)
    warnings = _alpha_warnings(
        has_alpha=has_alpha,
        alpha_min=alpha_min,
        alpha_max=alpha_max,
        visible_percent=visible_percent,
        bbox=bbox,
        image_size=rgba.size,
    )
    return AlphaDiagnostics(
        width=rgba.width,
        height=rgba.height,
        has_alpha=has_alpha,
        alpha_min=alpha_min,
        alpha_max=alpha_max,
        visible_percent=visible_percent,
        bbox=bbox,
        warnings=warnings,
    )


def analyze_alpha_file(path: Path) -> AlphaDiagnostics:
    """Open one image file and return alpha diagnostics for the GUI/tests."""

    with Image.open(path) as image:
        return analyze_alpha_image_object(image)
