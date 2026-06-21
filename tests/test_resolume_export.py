from pathlib import Path

from PIL import Image

from resolume_alpha_tool.core.resolume_export import (
    RESOLUME_CANVAS_SIZE,
    RESOLUME_OUTPUT_FORMAT,
    RESOLUME_OUTPUT_SUFFIX,
    build_resolume_output_path,
    export_resolume_image,
    resolume_processing_options,
)


def _write_image(path: Path) -> None:
    Image.new("RGBA", (8, 8), (10, 20, 30, 255)).save(path)


def test_resolume_processing_options_are_fixed() -> None:
    options = resolume_processing_options()

    assert options.remove_background is True
    assert options.output_format == RESOLUME_OUTPUT_FORMAT == "png"
    assert options.suffix == RESOLUME_OUTPUT_SUFFIX == "_resolume"
    assert options.fit_mode == "contain"
    assert (options.canvas_width, options.canvas_height) == RESOLUME_CANVAS_SIZE == (1920, 1080)
    assert options.overwrite is False


def test_build_resolume_output_path_uses_safe_suffix(tmp_path: Path) -> None:
    input_path = tmp_path / "asset.jpg"

    assert build_resolume_output_path(input_path, tmp_path) == tmp_path / "asset_resolume.png"


def test_build_resolume_output_path_avoids_overwrite(tmp_path: Path) -> None:
    input_path = tmp_path / "asset.jpg"
    (tmp_path / "asset_resolume.png").write_text("existing")

    assert build_resolume_output_path(input_path, tmp_path) == tmp_path / "asset_resolume_2.png"


def test_export_resolume_image_writes_png_without_rembg_when_monkeypatched(
    tmp_path: Path,
    monkeypatch,
) -> None:
    input_path = tmp_path / "asset.png"
    output_dir = tmp_path / "out"
    _write_image(input_path)

    def fake_options():
        options = resolume_processing_options()
        return type(options)(
            remove_background=False,
            rembg_model=options.rembg_model,
            alpha_threshold=options.alpha_threshold,
            feather_radius=0,
            alpha_gamma=options.alpha_gamma,
            despill_strength=0,
            fit_mode=options.fit_mode,
            canvas_width=options.canvas_width,
            canvas_height=options.canvas_height,
            output_format=options.output_format,
            suffix=options.suffix,
            overwrite=options.overwrite,
        )

    monkeypatch.setattr(
        "resolume_alpha_tool.core.resolume_export.resolume_processing_options",
        lambda model="u2net": fake_options(),
    )

    result = export_resolume_image(input_path, output_dir)

    assert result.output_path == (output_dir / "asset_resolume.png").resolve()
    assert result.width == 1920
    assert result.height == 1080
    assert result.background_removed is False
