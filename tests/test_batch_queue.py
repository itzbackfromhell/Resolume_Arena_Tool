from pathlib import Path

from PIL import Image

from resolume_alpha_tool.core.batch import process_files
from resolume_alpha_tool.core.batch_queue import (
    failed_input_paths,
    scan_export_queue,
    scan_file_export_queue,
)
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


def test_scan_export_queue_uses_collision_safe_single_output(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    source = input_dir / "asset.png"
    existing = output_dir / "asset_alpha.png"
    _write_image(source)
    _write_image(existing)

    items = scan_export_queue(
        source,
        output_dir,
        ProcessingOptions(output_format="png", overwrite=False),
        mode="single",
    )

    assert len(items) == 1
    assert items[0].input_path == source.resolve()
    assert items[0].output_path == (output_dir / "asset_alpha_2.png").resolve()
    assert items[0].status == "pending"


def test_scan_file_export_queue_uses_retry_export_naming(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    source = input_dir / "retry.png"
    _write_image(source)

    items = scan_file_export_queue(
        [source],
        output_dir,
        ProcessingOptions(output_format="webp", suffix="_arena", overwrite=False),
    )

    assert len(items) == 1
    assert items[0].input_path == source.resolve()
    assert items[0].output_path == (output_dir / "retry_arena.webp").resolve()
    assert items[0].status == "pending"


def test_scan_file_export_queue_marks_retry_collisions_as_skipped(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    source = input_dir / "retry.png"
    existing = output_dir / "retry_alpha.png"
    _write_image(source)
    _write_image(existing)

    items = scan_file_export_queue(
        [source],
        output_dir,
        ProcessingOptions(output_format="png", overwrite=False),
    )

    assert len(items) == 1
    assert items[0].input_path == source.resolve()
    assert items[0].output_path == existing.resolve()
    assert items[0].status == "skipped_existing"


def test_scan_file_export_queue_keeps_missing_retry_inputs_previewable(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    missing = tmp_path / "missing.png"

    items = scan_file_export_queue(
        [missing],
        output_dir,
        ProcessingOptions(output_format="png", overwrite=False),
    )

    assert len(items) == 1
    assert items[0].input_path == missing.resolve()
    assert items[0].output_path == (output_dir / "missing_alpha.png").resolve()
    assert items[0].status == "pending"


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


def test_process_files_collects_missing_retry_inputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    missing = tmp_path / "missing.png"

    summary = process_files([missing], output_dir, ProcessingOptions(output_format="png"))

    assert summary.processed == 0
    assert summary.failed == 1
    assert summary.skipped == 0
    assert str(missing) in summary.errors[0]


def test_failed_input_paths_extracts_paths() -> None:
    paths = failed_input_paths((r"C:\assets\bad.png: cannot decode image",))

    assert paths == (Path(r"C:\assets\bad.png"),)
