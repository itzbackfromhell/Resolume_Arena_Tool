from resolume_alpha_tool.ui.labels import (
    EDGE_PROFILE_LABELS,
    PREVIEW_MODE_LABELS,
    RESOLUME_PRESET_LABELS,
    TARGET_LABELS,
    preview_mode_keys,
    target_label,
)


def test_target_labels_cover_export_modes() -> None:
    assert TARGET_LABELS == {
        "resolume": "Resolume PNG",
        "shirt_print": "Shirt/Print PNG",
    }
    assert target_label("resolume") == "Resolume PNG"


def test_ui_choice_keys_are_stable() -> None:
    assert tuple(RESOLUME_PRESET_LABELS) == ("1080p", "4k", "square_1080")
    assert tuple(EDGE_PROFILE_LABELS) == ("normal", "soft", "tight", "grow")
    assert preview_mode_keys() == ("checker", "black", "white", "alpha", "bounds")
    assert PREVIEW_MODE_LABELS["bounds"] == "Bounds"
