from resolume_alpha_tool.cli import build_parser, main


def test_cli_parser_has_support_commands() -> None:
    parser = build_parser()
    commands = parser._subparsers._group_actions[0].choices  # noqa: SLF001

    assert "diagnostics" in commands
    assert "profiles" in commands
    assert "rembg-check" in commands


def test_profiles_command_prints_profiles(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["profiles"]) == 0

    output = capsys.readouterr().out
    assert "overlay_1080p" in output
