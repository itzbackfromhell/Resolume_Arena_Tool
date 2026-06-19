from pathlib import Path

from PIL import Image

from resolume_alpha_tool.core.input_resolver import clean_path_text, resolve_preview_source


def test_clean_path_text_removes_matching_quotes() -> None:
    assert clean_path_text('"image.png"') == "image.png"
    assert clean_path_text("'image.png'") == "image.png"


def test_resolve_preview_source_accepts_file(tmp_path: Path) -> None:
    image = tmp_path / "asset.PNG"
    Image.new("RGBA", (2, 2), (255, 0, 0, 255)).save(image)
    assert resolve_preview_source(image) == image


def test_resolve_preview_source_finds_first_image_in_folder(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    image = nested / "asset.webp"
    Image.new("RGBA", (2, 2), (255, 0, 0, 255)).save(image)
    assert resolve_preview_source(tmp_path) == image


def test_resolve_preview_source_rejects_missing_path(tmp_path: Path) -> None:
    assert resolve_preview_source(tmp_path / "missing.png") is None
