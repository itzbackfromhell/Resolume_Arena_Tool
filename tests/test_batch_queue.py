from pathlib import Path

from PIL import Image

from resolume_alpha_tool.core.batch import process_files
from resolume_alpha_tool.core.batch_queue import failed_input_paths, scan_export_queue
from resolume_alpha_tool.core.models import ProcessingOptions


def _write_image(path: Path) -> None:
    Image.new("RGBA", (2, 2), (255, 0, 0, 255)).save(path)


def test_scan_export_queue_marks_existing_outputs(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    source = input_dir / "asset.png"
    existing = output_dir / "asset_alpha.png"
    _write_image(source)
    _write_image(existing)

    items = scan_export_queue(
        input_dir,
        output_dir,
        ProcessingOptions(output_format="png", overwrite=False),
        mode="batch",
    )

    assert len(items) == 1
    assert items[0].input_path == source.resolve()
    assert items[0].output_path == existing.resolve()
    assert items[0].status == "skipped_existing"


def test_process_files_handles_explicit_retry_queue(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    source = input_dir / "retry.png"
    _write_image(source)

    summary = process_files([source], output_dir, ProcessingOptions(output_format="png"))

    assert summary.processed == 1
    assert summary.failed == 0
    assert summary.skipped == 0
    assert summary.results[0].input_path == source.resolve()


def test_failed_input_paths_extracts_paths() -> None:
    paths = failed_input_paths((r"C:\assets\bad.png: cannot decode image",))
    assert paths == (Path(r"C:\assets\bad.png"),)
