from resolume_alpha_tool.cli import main


def test_profiles_command_prints_profiles(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["profiles"]) == 0

    output = capsys.readouterr().out
    assert "overlay_1080p" in output


def test_diagnostics_command_writes_report(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    report = tmp_path / "diagnostic.json"

    assert main(["diagnostics", "--output", str(report)]) == 0

    assert report.exists()
    assert "Diagnostics written" in capsys.readouterr().out
