from pathlib import Path

from PIL import Image

from resolume_alpha_tool.core.batch import process_directory
from resolume_alpha_tool.core.models import ProcessingOptions


def _write_image(path: Path) -> None:
    Image.new("RGBA", (3, 3), (255, 0, 0, 255)).save(path)


def test_process_directory_reports_skipped_existing_files(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    source = input_dir / "asset.png"
    existing = output_dir / "asset_alpha.png"
    _write_image(source)
    _write_image(existing)

    messages: list[str] = []
    summary = process_directory(
        input_dir,
        output_dir,
        ProcessingOptions(output_format="png", overwrite=False),
        on_progress=messages.append,
    )

    assert summary.processed == 0
    assert summary.failed == 0
    assert summary.skipped == 1
    assert any(message.startswith("Skipped existing") for message in messages)


def test_process_directory_cancel_skips_remaining_files(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    for name in ("a.png", "b.png"):
        _write_image(input_dir / name)

    messages: list[str] = []
    summary = process_directory(
        input_dir,
        output_dir,
        ProcessingOptions(output_format="png"),
        on_progress=messages.append,
        should_cancel=lambda: True,
    )

    assert summary.processed == 0
    assert summary.failed == 0
    assert summary.skipped == 2
    assert messages == ["CANCELLED batch export; skipped remaining=2"]
