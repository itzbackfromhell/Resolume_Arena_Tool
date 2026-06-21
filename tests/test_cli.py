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
