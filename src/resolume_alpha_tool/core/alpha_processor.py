"""Image-processing pipeline for alpha assets."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageFilter

from .exceptions import DependencyMissingError, ProcessingError
from .models import ProcessingOptions, ProcessResult
from .rembg_runtime import create_rembg_session, import_rembg_symbols


@lru_cache(maxsize=8)
def _get_rembg_session(model_name: str):  # type: ignore[no-untyped-def]
    """Create and cache a rembg session for batch performance."""

    return create_rembg_session(model_name)


def _remove_background_with_rembg(image: Image.Image, model_name: str) -> Image.Image:
    _new_session, remove = import_rembg_symbols()
    session = _get_rembg_session(model_name)
    try:
        output = remove(image.convert("RGBA"), session=session)
    except Exception as exc:  # pragma: no cover - depends on optional runtime state
        raise ProcessingError(
            "rembg failed while removing the background. "
            f"Model: {model_name}. Original error: {exc}"
        ) from exc
    if not isinstance(output, Image.Image):  # pragma: no cover - defensive guard
        raise ProcessingError(f"rembg returned an unexpected output type: {type(output)!r}")
    return output.convert("RGBA")


def _apply_alpha_threshold(alpha: Image.Image, threshold: int) -> Image.Image:
    threshold = max(0, min(255, threshold))
    if threshold <= 0:
        return alpha
    return alpha.point(lambda value: 0 if value < threshold else value)


def _apply_alpha_gamma(alpha: Image.Image, gamma: float) -> Image.Image:
    if gamma <= 0 or abs(gamma - 1.0) < 0.001:
        return alpha
    inv = 1.0 / gamma
    table = [round(((i / 255.0) ** inv) * 255) for i in range(256)]
    return alpha.point(table)


def _despill_rgb(image: Image.Image, alpha: Image.Image, strength: float) -> Image.Image:
    """Reduce visible matte color in semi-transparent pixels.

    This is intentionally conservative: it darkens RGB values near low-alpha edges,
    which prevents light halos when Resolume composites the asset over dark visuals.
    """

    strength = max(0.0, min(1.0, strength))
    if strength <= 0:
        return image

    rgb = image.convert("RGB")
    darkened = ImageEnhance.Brightness(rgb).enhance(1.0 - (0.45 * strength))
    edge_mask = alpha.point(lambda value: int((1.0 - (value / 255.0)) * 255 * strength))
    mixed = Image.composite(darkened, rgb, edge_mask)
    mixed.putalpha(alpha)
    return mixed.convert("RGBA")


def _cleanup_transparent_rgb(image: Image.Image) -> Image.Image:
    """Set fully transparent pixels to black to avoid fringe garbage."""

    rgba = image.convert("RGBA")
    _r, _g, _b, a = rgba.split()
    zero_mask = a.point(lambda value: 255 if value == 0 else 0)
    black = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    return Image.composite(black, rgba, zero_mask).convert("RGBA")


def _fit_to_canvas(image: Image.Image, options: ProcessingOptions) -> Image.Image:
    if options.fit_mode == "none":
        return image
    if not options.canvas_width or not options.canvas_height:
        return image

    target_w = max(1, int(options.canvas_width))
    target_h = max(1, int(options.canvas_height))
    rgba = image.convert("RGBA")

    if options.fit_mode == "stretch":
        return rgba.resize((target_w, target_h), Image.Resampling.LANCZOS)

    src_w, src_h = rgba.size
    scale_x = target_w / src_w
    scale_y = target_h / src_h
    scale = min(scale_x, scale_y) if options.fit_mode == "contain" else max(scale_x, scale_y)
    new_size = (max(1, round(src_w * scale)), max(1, round(src_h * scale)))
    resized = rgba.resize(new_size, Image.Resampling.LANCZOS)

    if options.fit_mode == "cover":
        left = max(0, (new_size[0] - target_w) // 2)
        top = max(0, (new_size[1] - target_h) // 2)
        return resized.crop((left, top, left + target_w, top + target_h)).convert("RGBA")

    canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    left = (target_w - new_size[0]) // 2
    top = (target_h - new_size[1]) // 2
    canvas.alpha_composite(resized, (left, top))
    return canvas


def process_image_object(image: Image.Image, options: ProcessingOptions) -> Image.Image:
    """Process an in-memory image into a clean RGBA asset."""

    had_alpha = "A" in image.getbands()
    rgba = image.convert("RGBA")

    if options.remove_background:
        rgba = _remove_background_with_rembg(rgba, options.rembg_model)

    alpha = rgba.getchannel("A")
    alpha = _apply_alpha_threshold(alpha, options.alpha_threshold)

    if options.feather_radius > 0:
        alpha = alpha.filter(ImageFilter.GaussianBlur(radius=options.feather_radius))

    alpha = _apply_alpha_gamma(alpha, options.alpha_gamma)

    # Prevent blur from expanding alpha outside the original silhouette too much.
    if had_alpha and not options.remove_background:
        original_alpha = image.convert("RGBA").getchannel("A")
        alpha = ImageChops.darker(alpha, original_alpha)

    rgba.putalpha(alpha)
    rgba = _despill_rgb(rgba, alpha, options.despill_strength)

    if options.transparent_rgb_cleanup:
        rgba = _cleanup_transparent_rgb(rgba)

    return _fit_to_canvas(rgba, options)


def save_image(image: Image.Image, output_path: Path, options: ProcessingOptions) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and not options.overwrite:
        raise ProcessingError(f"Output already exists: {output_path}")

    fmt = options.output_format.lower()
    if fmt == "png":
        image.save(output_path, format="PNG", optimize=True)
    elif fmt == "webp":
        image.save(output_path, format="WEBP", quality=options.webp_quality, lossless=False)
    else:
        raise ProcessingError(f"Unsupported output format: {options.output_format}")

    if not output_path.exists():
        raise ProcessingError(f"Image save reported success, but output was not created: {output_path}")
    if output_path.stat().st_size <= 0:
        raise ProcessingError(f"Output file is empty: {output_path}")


def process_file(input_path: Path, output_path: Path, options: ProcessingOptions) -> ProcessResult:
    """Process one file and write the exported asset."""

    input_path = input_path.expanduser().resolve()
    output_path = output_path.expanduser().resolve()
    try:
        with Image.open(input_path) as img:
            had_alpha = "A" in img.getbands()
            processed = process_image_object(img, options)
        save_image(processed, output_path, options)
        width, height = processed.size
        return ProcessResult(
            input_path=input_path,
            output_path=output_path,
            width=width,
            height=height,
            had_alpha=had_alpha,
            background_removed=options.remove_background,
        )
    except Exception as exc:
        if isinstance(exc, ProcessingError | DependencyMissingError):
            raise
        raise ProcessingError(f"Could not process {input_path}: {exc}") from exc
