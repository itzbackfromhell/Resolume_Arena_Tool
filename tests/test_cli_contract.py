from resolume_alpha_tool.cli import build_parser, main


def test_cli_exposes_focused_professional_commands() -> None:
    parser = build_parser()
    subparsers = next(action for action in parser._actions if action.dest == "command")

    assert set(subparsers.choices) == {"batch", "convert", "profiles", "remove", "validate", "rembg-check", "version"}


def test_convert_command_uses_single_export_service(monkeypatch, tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    output_dir = tmp_path / "out"
    calls = []

    class Result:
        output_path = output_dir / "asset_resolume.png"
        width = 1920
        height = 1080

    def fake_export(input_path, target_dir, *, target, model, options, on_progress):  # type: ignore[no-untyped-def]
        calls.append((input_path, target_dir, target, model, options, on_progress))
        return Result()

    monkeypatch.setattr("resolume_alpha_tool.cli.export_alpha_image", fake_export)

    assert main(["convert", "input.png", str(output_dir), "--model", "isnet-general-use"]) == 0

    assert len(calls) == 1
    assert str(calls[0][0]) == "input.png"
    assert calls[0][1] == output_dir
    assert calls[0][2] == "resolume"
    assert calls[0][3] == "isnet-general-use"
    assert calls[0][4].rembg_model == "isnet-general-use"
    assert calls[0][4].canvas_width == 1920
    assert calls[0][4].canvas_height == 1080
    assert calls[0][4].fit_mode == "contain"
    assert callable(calls[0][5])
    assert "DONE" in capsys.readouterr().out


def test_convert_command_accepts_shirt_print_target(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    calls = []

    class Result:
        output_path = tmp_path / "out" / "asset_shirt_print.png"
        width = 700
        height = 500

    def fake_export(input_path, target_dir, *, target, model, options, on_progress):  # type: ignore[no-untyped-def]
        calls.append((target, model, options))
        return Result()

    monkeypatch.setattr("resolume_alpha_tool.cli.export_alpha_image", fake_export)

    assert main(["convert", "input.png", str(tmp_path / "out"), "--target", "shirt-print"]) == 0

    assert len(calls) == 1
    assert calls[0][0] == "shirt_print"
    assert calls[0][1] == "u2net"
    assert calls[0][2].rembg_model == "u2net"
    assert calls[0][2].padding == 96
    assert calls[0][2].canvas_width is None
    assert calls[0][2].canvas_height is None


def test_rembg_check_reports_failure_without_exiting(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr("resolume_alpha_tool.cli.runtime_summary", lambda: "runtime")

    def broken_healthcheck(model: str) -> str:
        raise RuntimeError(f"broken {model}")

    monkeypatch.setattr("resolume_alpha_tool.cli.rembg_healthcheck", broken_healthcheck)

    assert main(["rembg-check", "--model", "bad-model"]) == 1

    output = capsys.readouterr().out
    assert "Runtime: runtime" in output
    assert "rembg check failed: broken bad-model" in output
