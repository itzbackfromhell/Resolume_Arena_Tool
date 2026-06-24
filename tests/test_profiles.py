import pytest

from resolume_alpha_tool.core.exceptions import ProcessingError
from resolume_alpha_tool.core.profiles import (
    WorkflowProfile,
    built_in_profiles,
    get_profile,
    merge_profiles,
    normalize_profile_key,
    profile_from_json_object,
    profile_map,
)


def test_builtin_profiles_include_expected_workflows() -> None:
    profiles = built_in_profiles()
    keys = tuple(profile.key for profile in profiles)

    assert keys == (
        "resolume_1080p",
        "resolume_4k",
        "resolume_square_1080",
        "shirt_print_clean",
    )


def test_profile_key_aliases_resolve_to_builtin_keys() -> None:
    assert normalize_profile_key("Resolume") == "resolume_1080p"
    assert normalize_profile_key("shirt-print") == "shirt_print_clean"
    assert normalize_profile_key("square") == "resolume_square_1080"


def test_get_profile_resolves_alias() -> None:
    profile = get_profile("4k")

    assert profile.key == "resolume_4k"
    assert profile.target == "resolume"


def test_get_profile_reports_available_keys() -> None:
    with pytest.raises(ProcessingError, match="Available profiles"):
        get_profile("unknown")


def test_resolume_profile_builds_processing_options() -> None:
    options = get_profile("resolume_4k").to_processing_options()

    assert options.remove_background is True
    assert options.canvas_width == 3840
    assert options.canvas_height == 2160
    assert options.fit_mode == "contain"
    assert options.suffix == "_resolume"


def test_shirt_profile_builds_print_processing_options() -> None:
    options = get_profile("shirt").to_processing_options()

    assert options.remove_background is True
    assert options.trim_to_alpha is True
    assert options.canvas_width is None
    assert options.canvas_height is None
    assert options.padding == 96
    assert options.suffix == "_shirt_print"


def test_profile_from_json_object_normalizes_values() -> None:
    profile = profile_from_json_object(
        {
            "key": "My Profile",
            "label": "My Profile",
            "target": "shirt-print",
            "model": "u2netp",
            "resolume_preset": "1080p",
            "fit_mode": "cover",
            "edge_profile": "tight",
            "shirt_padding": "128",
            "overwrite": "yes",
            "description": "custom",
        }
    )

    assert profile.key == "my_profile"
    assert profile.target == "shirt_print"
    assert profile.model == "u2netp"
    assert profile.fit_mode == "cover"
    assert profile.edge_profile == "tight"
    assert profile.shirt_padding == 128
    assert profile.overwrite is True
    assert profile.description == "custom"


def test_profile_from_json_object_rejects_invalid_values() -> None:
    with pytest.raises(ProcessingError, match="fit mode"):
        profile_from_json_object({"key": "bad", "fit_mode": "crop"})


def test_merge_profiles_allows_user_override() -> None:
    user_profile = WorkflowProfile(
        key="resolume_1080p",
        label="Custom 1080",
        fit_mode="cover",
    )

    merged = merge_profiles(built_in_profiles(), (user_profile,))

    assert profile_map(merged)["resolume_1080p"].label == "Custom 1080"
    assert profile_map(merged)["resolume_1080p"].fit_mode == "cover"
    assert len(merged) == len(built_in_profiles())
