from pathlib import Path

from PIL import Image

from resolume_alpha_tool.core.batch_export import (
    BatchExportRequest,
    discover_images,
    export_batch,
    normalize_batch_targets,
)


def _write_image(path: Path) -> None:
    mode = "RGB" if path.suffix.lower() in {".jpg", ".jpeg"} else "RGBA"
    Image.new(mode, (8, 8), (255, 255, 255, 255)).save(path)


def _fake_export(input_path: Path, output_dir: Path, **_kwargs):  # type: ignore[no-untyped-def]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{input_path.stem}.png"
    _write_image(output_path)
    return type("Result", (), {"output_path": output_path})()


def test_discover_images_returns_supported_files_only(tmp_path: Path) -> None:
    _write_image(tmp_path / "b.png")
    _write_image(tmp_path / "a.jpg")
    (tmp_path / "notes.txt").write_text("nope")

    assert [path.name for path in discover_images(tmp_path)] == ["a.jpg", "b.png"]


def test_normalize_batch_targets_keeps_order_and_uniqueness() -> None:
    assert normalize_batch_targets(["resolume", "shirt-print", "resolume"]) == (
        "resolume",
        "shirt_print",
    )


def test_export_batch_collects_success_and_failure(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    good = tmp_path / "good.png"
    bad = tmp_path / "bad.png"
    _write_image(good)
    _write_image(bad)

    def fake_export(input_path: Path, output_dir: Path, **_kwargs):  # type: ignore[no-untyped-def]
        if input_path.name == "bad.png":
            raise RuntimeError("boom")
        return _fake_export(input_path, output_dir)

    monkeypatch.setattr("resolume_alpha_tool.core.batch_export.export_alpha_image", fake_export)

    summary = export_batch(BatchExportRequest(input_dir=tmp_path, output_dir=tmp_path / "out"))

    assert summary.total_count == 2
    assert summary.exported_count == 1
    assert summary.failed_count == 1
