from pathlib import Path

from PIL import Image

from resolume_alpha_tool.core.file_watcher import watch_folder
from resolume_alpha_tool.core.models import ProcessingOptions


def _write_image(path: Path) -> None:
    Image.new("RGBA", (2, 2), (255, 0, 0, 255)).save(path)


def test_watch_folder_processes_new_files_once(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    source = input_dir / "asset.png"
    _write_image(source)
    messages: list[str] = []

    watch_folder(
        input_dir,
        output_dir,
        ProcessingOptions(output_format="png"),
        interval_seconds=0.25,
        on_progress=messages.append,
        stop_after_cycles=2,
    )

    assert (output_dir / "asset_alpha.png").exists()
    assert messages.count("Saved asset_alpha.png") == 1
