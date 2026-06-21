from pathlib import Path

from PIL import Image

from resolume_alpha_tool import cli
from resolume_alpha_tool.core.batch_export import BatchExportSummary
from resolume_alpha_tool.core.exceptions import ProcessingError


def test_cli_convert_reports_project_errors(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    def fake_export(*_args, **_kwargs):
        raise ProcessingError("boom")

    monkeypatch.setattr(cli, "export_alpha_image", fake_export)

    exit_code = cli.main(["convert", "input.png", "out"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "ERROR: boom" in captured.err


def test_cli_batch_reports_summary(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    def fake_batch(request, **_kwargs):  # type: ignore[no-untyped-def]
        return BatchExportSummary(input_dir=request.input_dir, output_dir=request.output_dir)

    monkeypatch.setattr(cli, "export_batch", fake_batch)

    exit_code = cli.main(["batch", "input", "out", "--target", "shirt-print"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "DONE batch" in captured.out


def test_cli_remove_alias_passes_professional_options(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    def fake_export(input_path, output_dir, **kwargs):  # type: ignore[no-untyped-def]
        options = kwargs["options"]
        assert Path(input_path) == Path("input.png")
        assert Path(output_dir) == Path("out")
        assert kwargs["target"] == "shirt_print"
        assert options.rembg_model == "u2netp"
        assert options.padding == 42
        assert options.overwrite is True
        return type("Result", (), {"output_path": Path("out/asset.png"), "width": 8, "height": 8})()

    monkeypatch.setattr(cli, "export_alpha_image", fake_export)

    exit_code = cli.main(
        [
            "remove",
            "input.png",
            "out",
            "--target",
            "shirt-print",
            "--model",
            "u2netp",
            "--shirt-padding",
            "42",
            "--overwrite",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "DONE" in captured.out


def test_cli_batch_builds_options_for_requested_targets(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def fake_batch(request, **_kwargs):  # type: ignore[no-untyped-def]
        assert request.targets == ("resolume", "shirt_print")
        assert request.options_by_target["resolume"].canvas_width == 3840
        assert request.options_by_target["resolume"].fit_mode == "cover"
        assert request.options_by_target["shirt_print"].padding == 24
        return BatchExportSummary(input_dir=request.input_dir, output_dir=request.output_dir)

    monkeypatch.setattr(cli, "export_batch", fake_batch)

    exit_code = cli.main(
        [
            "batch",
            "input",
            "out",
            "--target",
            "resolume",
            "--target",
            "shirt-print",
            "--preset",
            "4k",
            "--fit",
            "cover",
            "--shirt-padding",
            "24",
        ]
    )

    assert exit_code == 0


def test_cli_validate_reports_valid_alpha_png(tmp_path: Path, capsys) -> None:
    output = tmp_path / "asset.png"
    image = Image.new("RGBA", (8, 8), (255, 255, 255, 255))
    image.putpixel((0, 0), (0, 0, 0, 0))
    image.save(output)

    exit_code = cli.main(["validate", str(output), "--target", "shirt-print"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "VALID" in captured.out
