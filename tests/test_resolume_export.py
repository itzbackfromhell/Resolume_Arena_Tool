from pathlib import Path

import pytest
from PIL import Image

from resolume_alpha_tool.core.exceptions import ProcessingError
from resolume_alpha_tool.core.resolume_export import (
    RESOLUME_CANVAS_SIZE,
    RESOLUME_OUTPUT_FORMAT,
    RESOLUME_OUTPUT_SUFFIX,
    SHIRT_PRINT_OUTPUT_SUFFIX,
    build_alpha_output_path,
    build_resolume_output_path,
    export_alpha_image,
    export_resolume_image,
    normalize_export_target,
    processing_options_for_target,
    resolume_processing_options,
    shirt_print_processing_options,
)


def _write_image(path: Path, size: tuple[int, int] = (8, 8)) -> None:
    Image.new("RGBA", size, (10, 20, 30, 255)).save(path)


def _fake_removed_background(image: Image.Image, _model: str) -> Image.Image:
    rgba = image.convert("RGBA")
    rgba.putpixel((0, 0), (0, 0, 0, 0))
    return rgba


def test_resolume_processing_options_are_fixed() -> None:
    options = resolume_processing_options()

    assert options.remove_background is True
    assert options.output_format == RESOLUME_OUTPUT_FORMAT == "png"
    assert options.suffix == RESOLUME_OUTPUT_SUFFIX == "_resolume"
    assert options.fit_mode == "contain"
    assert options.trim_to_alpha is False
    assert (options.canvas_width, options.canvas_height) == RESOLUME_CANVAS_SIZE == (1920, 1080)
    assert options.overwrite is False


def test_shirt_print_processing_options_are_fixed() -> None:
    options = shirt_print_processing_options()

    assert options.remove_background is True
    assert options.output_format == RESOLUME_OUTPUT_FORMAT == "png"
    assert options.suffix == SHIRT_PRINT_OUTPUT_SUFFIX == "_shirt_print"
    assert options.fit_mode == "none"
    assert options.trim_to_alpha is True
    assert options.padding == 96
    assert options.canvas_width is None
    assert options.canvas_height is None
    assert options.alpha_threshold > resolume_processing_options().alpha_threshold


def test_normalize_export_target_accepts_cli_spelling() -> None:
    assert normalize_export_target("shirt-print") == "shirt_print"
    assert normalize_export_target("shirt_print") == "shirt_print"
    assert normalize_export_target("resolume") == "resolume"


def test_build_resolume_output_path_uses_safe_suffix(tmp_path: Path) -> None:
    input_path = tmp_path / "asset.jpg"

    assert build_resolume_output_path(input_path, tmp_path) == tmp_path / "asset_resolume.png"


def test_build_alpha_output_path_uses_shirt_print_suffix(tmp_path: Path) -> None:
    input_path = tmp_path / "asset.jpg"

    assert build_alpha_output_path(input_path, tmp_path, target="shirt_print") == tmp_path / "asset_shirt_print.png"


def test_build_resolume_output_path_avoids_overwrite(tmp_path: Path) -> None:
    input_path = tmp_path / "asset.jpg"
    (tmp_path / "asset_resolume.png").write_text("existing")

    assert build_resolume_output_path(input_path, tmp_path) == tmp_path / "asset_resolume_2.png"


def test_export_resolume_image_requires_background_removal(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    input_path = tmp_path / "asset.png"
    _write_image(input_path)

    def fake_options(_model: str = "u2net"):
        options = resolume_processing_options()
        return type(options)(
            remove_background=False,
            rembg_model=options.rembg_model,
            alpha_threshold=options.alpha_threshold,
            feather_radius=0,
            alpha_gamma=options.alpha_gamma,
            despill_strength=0,
            trim_to_alpha=options.trim_to_alpha,
            padding=options.padding,
            fit_mode=options.fit_mode,
            canvas_width=options.canvas_width,
            canvas_height=options.canvas_height,
            output_format=options.output_format,
            suffix=options.suffix,
            overwrite=options.overwrite,
        )

    monkeypatch.setattr(
        "resolume_alpha_tool.core.resolume_export.resolume_processing_options",
        fake_options,
    )

    with pytest.raises(ProcessingError, match="background removal disabled"):
        export_resolume_image(input_path, tmp_path / "out")


def test_export_resolume_image_writes_valid_background_removed_png(
    tmp_path: Path,
    monkeypatch,
) -> None:
    input_path = tmp_path / "asset.png"
    output_dir = tmp_path / "out"
    _write_image(input_path)
    monkeypatch.setattr(
        "resolume_alpha_tool.core.alpha_processor._remove_background_with_rembg",
        _fake_removed_background,
    )

    result = export_resolume_image(input_path, output_dir)

    assert result.output_path == (output_dir / "asset_resolume.png").resolve()
    assert result.width == 1920
    assert result.height == 1080
    assert result.background_removed is True
    with Image.open(result.output_path) as image:
        assert image.format == "PNG"
        assert image.size == RESOLUME_CANVAS_SIZE
        assert image.convert("RGBA").getchannel("A").getextrema()[0] < 255


def test_export_alpha_image_writes_trimmed_shirt_print_png(
    tmp_path: Path,
    monkeypatch,
) -> None:
    input_path = tmp_path / "asset.png"
    output_dir = tmp_path / "out"
    _write_image(input_path, size=(100, 80))
    monkeypatch.setattr(
        "resolume_alpha_tool.core.alpha_processor._remove_background_with_rembg",
        _fake_removed_background,
    )

    result = export_alpha_image(input_path, output_dir, target="shirt-print")

    assert result.output_path == (output_dir / "asset_shirt_print.png").resolve()
    assert result.background_removed is True
    assert result.width < 1920
    assert result.height < 1080
    with Image.open(result.output_path) as image:
        assert image.format == "PNG"
        assert image.convert("RGBA").getchannel("A").getextrema()[0] < 255


def test_processing_options_for_target_returns_print_profile() -> None:
    assert processing_options_for_target("shirt-print") == shirt_print_processing_options()


def test_export_resolume_image_rejects_fully_opaque_background_output(
    tmp_path: Path,
    monkeypatch,
) -> None:
    input_path = tmp_path / "asset.png"
    output_dir = tmp_path / "out"
    _write_image(input_path, size=(16, 9))
    monkeypatch.setattr(
        "resolume_alpha_tool.core.alpha_processor._remove_background_with_rembg",
        lambda image, _model: image.convert("RGBA"),
    )

    with pytest.raises(ProcessingError, match="fully opaque PNG"):
        export_resolume_image(input_path, output_dir)

    assert not (output_dir / "asset_resolume.png").exists()
