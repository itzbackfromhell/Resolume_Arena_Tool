"""Preview helpers for alpha PNG QA and future GUI tools."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw

CHECKER_DARK = (32, 32, 32, 255)
CHECKER_LIGHT = (96, 96, 96, 255)
PREVIEW_BACKGROUNDS = ("checker", "black", "white", "alpha", "bounds")


@dataclass(frozen=True)
class PreviewRenderResult:
    """Result of one preview render."""

    image: Image.Image
    mode: str
    alpha_bbox: tuple[int, int, int, int] | None


def alpha_bbox(image: Image.Image, *, threshold: int = 1) -> tuple[int, int, int, int] | None:
    """Return the visible-alpha bounding box for an image."""

    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    if threshold > 1:
        alpha = alpha.point(lambda value: 255 if value >= threshold else 0)
    return alpha.getbbox()


def checkerboard(size: tuple[int, int], *, tile_size: int = 16) -> Image.Image:
    """Create a transparent-preview checkerboard image."""

    width, height = size
    canvas = Image.new("RGBA", size, CHECKER_DARK)
    draw = ImageDraw.Draw(canvas)
    tile = max(1, int(tile_size))
    for y in range(0, height, tile):
        for x in range(0, width, tile):
            if ((x // tile) + (y // tile)) % 2:
                draw.rectangle((x, y, min(x + tile, width), min(y + tile, height)), fill=CHECKER_LIGHT)
    return canvas


def alpha_matte(image: Image.Image) -> Image.Image:
    """Render an image's alpha channel as an opaque grayscale matte."""

    alpha = image.convert("RGBA").getchannel("A")
    return Image.merge("RGBA", (alpha, alpha, alpha, Image.new("L", alpha.size, 255)))


def render_preview(image: Image.Image, *, mode: str = "checker", tile_size: int = 16) -> PreviewRenderResult:
    """Render a QA preview for one alpha image."""

    normalized_mode = mode.strip().lower().replace("-", "_")
    rgba = image.convert("RGBA")
    bounds = alpha_bbox(rgba)

    if normalized_mode == "alpha":
        rendered = alpha_matte(rgba)
    elif normalized_mode == "black":
        rendered = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
        rendered.alpha_composite(rgba)
    elif normalized_mode == "white":
        rendered = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        rendered.alpha_composite(rgba)
    else:
        rendered = checkerboard(rgba.size, tile_size=tile_size)
        rendered.alpha_composite(rgba)

    if normalized_mode == "bounds" and bounds is not None:
        draw = ImageDraw.Draw(rendered)
        left, top, right, bottom = bounds
        draw.rectangle((left, top, max(left, right - 1), max(top, bottom - 1)), outline=(57, 255, 20, 255), width=2)

    return PreviewRenderResult(image=rendered, mode=normalized_mode, alpha_bbox=bounds)
