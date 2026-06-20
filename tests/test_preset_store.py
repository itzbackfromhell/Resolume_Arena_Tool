import pytest

from resolume_alpha_tool.core.models import ProcessingOptions
from resolume_alpha_tool.core.preset_store import (
    CUSTOM_PRESET_NAME,
    clean_preset_name,
    merge_presets,
    normalize_preset,
    normalize_presets,
    preset_from_options,
)


def test_clean_preset_name_normalizes_spacing() -> None:
    assert clean_preset_name("  Dark   VJ   Glow  ") == "Dark VJ Glow"


@pytest.mark.parametrize("name", ["", "Custom", "bad/name", "bad:name"])
def test_clean_preset_name_rejects_invalid_names(name: str) -> None:
    with pytest.raises(ValueError):
        clean_preset_name(name)


def test_normalize_preset_keeps_processing_fields_only() -> None:
    assert normalize_preset({"alpha_threshold": 12, "unknown": "nope"}) == {"alpha_threshold": 12}


def test_normalize_presets_keeps_valid_entries() -> None:
    presets = normalize_presets({" My Preset ": {"output_format": "png"}, "empty": {}})
    assert presets == {"My Preset": {"output_format": "png"}}


def test_merge_presets_allows_user_override() -> None:
    merged = merge_presets({"clean": {"alpha_threshold": 8}}, {"clean": {"alpha_threshold": 32}})
    assert merged["clean"]["alpha_threshold"] == 32


def test_preset_from_options_includes_suffix() -> None:
    preset = preset_from_options(ProcessingOptions(suffix="_vj"))
    assert preset["suffix"] == "_vj"
    assert CUSTOM_PRESET_NAME == "Custom"
