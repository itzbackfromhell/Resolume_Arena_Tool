import json
from pathlib import Path

from resolume_alpha_tool.core.diagnostics import build_diagnostics_payload, write_diagnostics_report
from resolume_alpha_tool.core.resolume_profiles import PROFILES, get_profile, profile_output_dir
from resolume_alpha_tool.core.resources import default_preset_path, portable_output_dir


def test_default_preset_path_exists() -> None:
    assert default_preset_path().name == "defaults.json"
    assert default_preset_path().exists()


def test_portable_output_dir_is_named_output() -> None:
    assert portable_output_dir().name == "output"


def test_diagnostics_payload_contains_runtime_and_paths() -> None:
    payload = build_diagnostics_payload()

    assert payload["app"]["name"] == "Resolume Alpha Dropper"
    assert "python" in payload
    assert payload["paths"]["default_preset_exists"] is True


def test_write_diagnostics_report_writes_json(tmp_path: Path) -> None:
    report = write_diagnostics_report(tmp_path / "diagnostic.json")

    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["app"]["name"] == "Resolume Alpha Dropper"


def test_resolume_profiles_have_export_options(tmp_path: Path) -> None:
    assert "overlay_1080p" in PROFILES
    profile = get_profile("overlay_1080p")

    assert profile.options.canvas_width == 1920
    assert profile_output_dir(tmp_path, profile) == tmp_path / profile.suggested_folder
