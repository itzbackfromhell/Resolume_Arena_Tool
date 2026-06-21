from pathlib import Path

from PIL import Image

from resolume_alpha_tool.core.input_resolver import clean_path_text, is_supported_image


def test_clean_path_text_removes_matching_quotes() -> None:
    assert clean_path_text('"image.png"') == "image.png"
    assert clean_path_text("'image.png'") == "image.png"


def test_is_supported_image_accepts_image_file(tmp_path: Path) -> None:
    image = tmp_path / "asset.PNG"
    Image.new("RGBA", (2, 2), (255, 0, 0, 255)).save(image)

    assert is_supported_image(image) is True


def test_is_supported_image_rejects_missing_path(tmp_path: Path) -> None:
    assert is_supported_image(tmp_path / "missing.png") is False
