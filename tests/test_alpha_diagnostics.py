from pathlib import Path

from PIL import Image

from resolume_alpha_tool.core.alpha_diagnostics import (
    analyze_alpha_file,
    analyze_alpha_image_object,
)


def test_alpha_diagnostics_detects_fully_opaque_input() -> None:
    image = Image.new("RGB", (10, 10), (255, 0, 0))

    diagnostics = analyze_alpha_image_object(image)

    assert diagnostics.width == 10
    assert diagnostics.height == 10
    assert diagnostics.has_alpha is False
    assert diagnostics.alpha_min == 255
    assert diagnostics.alpha_max == 255
    assert diagnostics.visible_percent == 100.0
    assert diagnostics.warnings


def test_alpha_diagnostics_detects_tiny_visible_motif(tmp_path: Path) -> None:
    path = tmp_path / "tiny.png"
    image = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    image.putpixel((10, 10), (255, 255, 255, 255))
    image.save(path)

    diagnostics = analyze_alpha_file(path)

    assert diagnostics.has_alpha is True
    assert diagnostics.alpha_min == 0
    assert diagnostics.alpha_max == 255
    assert diagnostics.visible_percent < 1.0
    assert diagnostics.bbox == (10, 10, 11, 11)
    assert any("very small" in warning for warning in diagnostics.warnings)
