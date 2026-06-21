from resolume_alpha_tool.cli import build_parser, main


def test_cli_exposes_only_focused_commands() -> None:
    parser = build_parser()
    subparsers = next(action for action in parser._actions if action.dest == "command")

    assert set(subparsers.choices) == {"convert", "rembg-check"}


def test_convert_command_uses_single_export_service(monkeypatch, tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    output_dir = tmp_path / "out"
    calls = []

    class Result:
        output_path = output_dir / "asset_resolume.png"
        width = 1920
        height = 1080

    def fake_export(input_path, target_dir, *, target, model, on_progress):  # type: ignore[no-untyped-def]
        calls.append((input_path, target_dir, target, model, on_progress))
        return Result()

    monkeypatch.setattr("resolume_alpha_tool.cli.export_alpha_image", fake_export)

    assert main(["convert", "input.png", str(output_dir), "--model", "isnet-general-use"]) == 0

    assert len(calls) == 1
    assert str(calls[0][0]) == "input.png"
    assert calls[0][1] == output_dir
    assert calls[0][2] == "resolume"
    assert calls[0][3] == "isnet-general-use"
    assert callable(calls[0][4])
    assert "DONE" in capsys.readouterr().out


def test_convert_command_accepts_shirt_print_target(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    calls = []

    class Result:
        output_path = tmp_path / "out" / "asset_shirt_print.png"
        width = 700
        height = 500

    def fake_export(input_path, target_dir, *, target, model, on_progress):  # type: ignore[no-untyped-def]
        calls.append((target, model))
        return Result()

    monkeypatch.setattr("resolume_alpha_tool.cli.export_alpha_image", fake_export)

    assert main(["convert", "input.png", str(tmp_path / "out"), "--target", "shirt-print"]) == 0

    assert calls == [("shirt_print", "u2net")]


def test_rembg_check_reports_failure_without_exiting(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr("resolume_alpha_tool.cli.runtime_summary", lambda: "runtime")

    def broken_healthcheck(model: str) -> str:
        raise RuntimeError(f"broken {model}")

    monkeypatch.setattr("resolume_alpha_tool.cli.rembg_healthcheck", broken_healthcheck)

    assert main(["rembg-check", "--model", "bad-model"]) == 1

    output = capsys.readouterr().out
    assert "Runtime: runtime" in output
    assert "rembg check failed: broken bad-model" in output
