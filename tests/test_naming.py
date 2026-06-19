from pathlib import Path

from resolume_alpha_tool.core.naming import build_output_path


def test_build_output_path_uses_suffix_and_extension(tmp_path: Path) -> None:
    result = build_output_path(Path("photo.jpg"), tmp_path, suffix="_alpha", extension="png")
    assert result == tmp_path / "photo_alpha.png"


def test_build_output_path_avoids_collision(tmp_path: Path) -> None:
    first = tmp_path / "photo_alpha.png"
    first.write_text("x")
    result = build_output_path(Path("photo.jpg"), tmp_path, suffix="_alpha", extension="png")
    assert result == tmp_path / "photo_alpha_2.png"
