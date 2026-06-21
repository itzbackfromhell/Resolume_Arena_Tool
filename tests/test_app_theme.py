import pytest

from resolume_alpha_tool.app import (
    DARK_CHECKER_ALT,
    DARK_CHECKER_BASE,
    DARK_THEME,
    _hex_to_windows_colorref,
)


def test_dark_theme_defines_required_palette_tokens() -> None:
    required = {
        "background",
        "panel",
        "panel_alt",
        "field",
        "text",
        "muted",
        "disabled",
        "heading",
        "accent",
        "accent_hover",
        "accent_pressed",
        "border",
        "error",
    }

    assert required <= DARK_THEME.keys()
    assert DARK_THEME["background"] == "#000000"
    assert DARK_THEME["panel"] == "#000000"
    assert DARK_THEME["field"] == "#000000"
    assert DARK_THEME["heading"] == "#39ff14"


def test_dark_checkerboard_uses_opaque_rgba_colors() -> None:
    assert len(DARK_CHECKER_BASE) == 4
    assert len(DARK_CHECKER_ALT) == 4
    assert DARK_CHECKER_BASE[-1] == 255
    assert DARK_CHECKER_ALT[-1] == 255
    assert DARK_CHECKER_BASE != DARK_CHECKER_ALT


def test_hex_to_windows_colorref_converts_rgb_to_bgr_integer() -> None:
    assert _hex_to_windows_colorref("#000000") == 0x000000
    assert _hex_to_windows_colorref("#39ff14") == 0x14FF39
    assert _hex_to_windows_colorref("#164d12") == 0x124D16


def test_hex_to_windows_colorref_rejects_invalid_color() -> None:
    with pytest.raises(ValueError, match="Expected #RRGGBB"):
        _hex_to_windows_colorref("#fff")
