from pathlib import Path

from PIL import Image

from resolume_alpha_tool.core.batch import process_directory
from resolume_alpha_tool.core.models import ProcessingOptions


def test_process_directory_processes_images(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(input_dir / "a.png")
    Image.new("RGB", (4, 4), (0, 255, 0)).save(input_dir / "b.jpg")

    summary = process_directory(
        input_dir,
        output_dir,
        ProcessingOptions(feather_radius=0, despill_strength=0),
    )

    assert summary.processed == 2
    assert summary.failed == 0
    assert len(list(output_dir.glob("*.png"))) == 2
