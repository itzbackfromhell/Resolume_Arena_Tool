from resolume_alpha_tool import cli
from resolume_alpha_tool.core.exceptions import ProcessingError


def test_cli_convert_reports_project_errors(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    def fake_export(*_args, **_kwargs):
        raise ProcessingError("boom")

    monkeypatch.setattr(cli, "export_alpha_image", fake_export)

    exit_code = cli.main(["convert", "input.png", "out"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "ERROR: boom" in captured.err
