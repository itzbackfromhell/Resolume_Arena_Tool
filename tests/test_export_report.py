import json
from pathlib import Path

from PIL import Image

from resolume_alpha_tool.core.batch import process_files
from resolume_alpha_tool.core.export_report import build_report_payload, write_export_report
from resolume_alpha_tool.core.models import ProcessingOptions


def test_export_report_payload_contains_summary(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    source = input_dir / "asset.png"
    Image.new("RGBA", (2, 2), (255, 0, 0, 255)).save(source)
    options = ProcessingOptions(output_format="png")
    summary = process_files([source], output_dir, options)

    payload = build_report_payload(
        mode="batch",
        input_path=input_dir,
        output_dir=output_dir,
        options=options,
        summary=summary,
        skipped_existing=("already.png",),
    )

    assert payload["summary"] == {"processed": 1, "failed": 0, "skipped": 0}
    assert payload["results"][0]["output_path"].endswith("asset_alpha.png")
    assert payload["skipped_existing"] == ["already.png"]


def test_write_export_report_writes_json(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    source = input_dir / "asset.png"
    Image.new("RGBA", (2, 2), (255, 0, 0, 255)).save(source)
    options = ProcessingOptions(output_format="png")
    summary = process_files([source], output_dir, options)
    report = write_export_report(
        report_path=output_dir / "report.json",
        mode="batch",
        input_path=input_dir,
        output_dir=output_dir,
        options=options,
        summary=summary,
    )

    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["summary"]["processed"] == 1
    assert data["mode"] == "batch"
