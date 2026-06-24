import json

from resolume_alpha_tool.core.profile_store import load_available_profiles, load_user_profiles, save_user_profiles
from resolume_alpha_tool.core.profiles import WorkflowProfile, profile_map


def test_load_user_profiles_returns_empty_for_missing_file(tmp_path) -> None:
    assert load_user_profiles(tmp_path / "missing.json") == ()


def test_save_and_load_user_profiles_roundtrip(tmp_path) -> None:
    path = tmp_path / "profiles.json"
    profile = WorkflowProfile(key="custom", label="Custom", fit_mode="cover")

    saved_path = save_user_profiles((profile,), path)

    assert saved_path == path
    assert json.loads(path.read_text(encoding="utf-8"))["profiles"][0]["key"] == "custom"
    assert load_user_profiles(path) == (profile,)


def test_invalid_user_profile_entries_are_skipped(tmp_path) -> None:
    path = tmp_path / "profiles.json"
    path.write_text(
        json.dumps(
            {
                "profiles": [
                    {"key": "valid", "label": "Valid"},
                    {"key": "broken", "fit_mode": "crop"},
                    "not-an-object",
                ]
            }
        ),
        encoding="utf-8",
    )

    profiles = load_user_profiles(path)

    assert tuple(profile.key for profile in profiles) == ("valid",)


def test_load_available_profiles_merges_user_overrides(tmp_path) -> None:
    path = tmp_path / "profiles.json"
    save_user_profiles((WorkflowProfile(key="resolume_1080p", label="My Default", fit_mode="cover"),), path)

    profiles = profile_map(load_available_profiles(path))

    assert profiles["resolume_1080p"].label == "My Default"
    assert profiles["resolume_1080p"].fit_mode == "cover"
    assert "resolume_4k" in profiles
