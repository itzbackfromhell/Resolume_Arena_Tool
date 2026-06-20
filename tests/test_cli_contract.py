from pathlib import Path

from resolume_alpha_tool import cli
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


def test_preset_rembg_model_is_not_overwritten_by_cli_default(
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    preset_path = tmp_path / "defaults.json"
    preset_path.write_text(
        '{"custom_rembg": {"remove_background": true, "rembg_model": "isnet-general-use"}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "DEFAULT_PRESET_PATH", preset_path)

    parser = cli.build_parser()
    args = parser.parse_args(["remove", "input.png", "output", "--preset", "custom_rembg"])

    options = cli._build_options(args)

    assert options.remove_background is True
    assert options.rembg_model == "isnet-general-use"


def test_model_flag_overrides_preset_rembg_model(
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    preset_path = tmp_path / "defaults.json"
    preset_path.write_text(
        '{"custom_rembg": {"remove_background": true, "rembg_model": "isnet-general-use"}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "DEFAULT_PRESET_PATH", preset_path)

    parser = cli.build_parser()
    args = parser.parse_args(
        ["remove", "input.png", "output", "--preset", "custom_rembg", "--model", "u2netp"]
    )

    options = cli._build_options(args)

    assert options.remove_background is True
    assert options.rembg_model == "u2netp"
