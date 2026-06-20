import json

from resolume_alpha_tool.core import gui_settings


def test_gui_settings_uses_override_config_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("RESOLUME_ALPHA_DROPPER_CONFIG_DIR", str(tmp_path))
    assert gui_settings.config_dir() == tmp_path
    assert gui_settings.settings_path() == tmp_path / "settings.json"
    assert gui_settings.user_presets_path() == tmp_path / "user_presets.json"


def test_json_object_roundtrip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    gui_settings.save_json_object(path, {"output_dir": "D:/Assets", "overwrite": True})
    assert json.loads(path.read_text(encoding="utf-8"))["overwrite"] is True
    assert gui_settings.load_json_object(path)["output_dir"] == "D:/Assets"


def test_load_json_object_rejects_non_object(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("[]", encoding="utf-8")
    assert gui_settings.load_json_object(path) == {}
