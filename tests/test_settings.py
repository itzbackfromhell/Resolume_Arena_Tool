import json

from resolume_alpha_tool.core import settings


def test_settings_paths_use_current_override_config_dir(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv(settings.CONFIG_ENV_VAR, str(tmp_path))

    assert settings.config_dir() == tmp_path
    assert settings.settings_path() == tmp_path / settings.SETTINGS_FILE_NAME
    assert settings.user_presets_path() == tmp_path / settings.USER_PRESETS_FILE_NAME


def test_sanitize_settings_normalizes_known_choices() -> None:
    app_settings = settings.sanitize_settings(
        {
            "export_target": "shirt-print",
            "resolume_preset": "square-1080",
            "fit_mode": "cover",
            "preview_mode": "alpha",
            "edge_profile": "tight",
            "shirt_padding": "2048",
            "batch_both_targets": "yes",
            "batch_recursive": "true",
            "open_after_export": "on",
        }
    )

    assert app_settings.export_target == "shirt_print"
    assert app_settings.resolume_preset == "square_1080"
    assert app_settings.fit_mode == "cover"
    assert app_settings.preview_mode == "alpha"
    assert app_settings.edge_profile == "tight"
    assert app_settings.shirt_padding == 320
    assert app_settings.batch_both_targets is True
    assert app_settings.batch_recursive is True
    assert app_settings.open_after_export is True


def test_sanitize_settings_replaces_invalid_values() -> None:
    app_settings = settings.sanitize_settings(
        {
            "export_target": "broken",
            "resolume_preset": "huge",
            "fit_mode": "crop",
            "preview_mode": "neon",
            "edge_profile": "knife",
            "shirt_padding": "not-a-number",
        }
    )

    assert app_settings.export_target == "resolume"
    assert app_settings.resolume_preset == "1080p"
    assert app_settings.fit_mode == "contain"
    assert app_settings.preview_mode == "checker"
    assert app_settings.edge_profile == "normal"
    assert app_settings.shirt_padding == 96


def test_app_settings_roundtrip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    app_settings = settings.AppSettings(output_dir="D:/Assets", batch_recursive=True, shirt_padding=128)

    settings.save_app_settings(app_settings, path)
    loaded = settings.load_app_settings(path)

    assert loaded == app_settings
    assert json.loads(path.read_text(encoding="utf-8"))["batch_recursive"] is True


def test_load_app_settings_recovers_from_invalid_json(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("[]", encoding="utf-8")

    assert settings.load_app_settings(path) == settings.AppSettings()


def test_app_settings_keys_are_stable_for_gui_migration() -> None:
    assert settings.app_settings_keys() == (
        "input_path",
        "batch_dir",
        "output_dir",
        "export_target",
        "resolume_preset",
        "fit_mode",
        "preview_mode",
        "edge_profile",
        "shirt_padding",
        "batch_both_targets",
        "batch_recursive",
        "open_after_export",
        "window_geometry",
    )
