from PIL import Image

from resolume_alpha_tool.core.preview_tools import alpha_bbox, alpha_matte, checkerboard, render_preview


def test_alpha_bbox_returns_visible_bounds() -> None:
    image = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    image.putpixel((2, 3), (255, 255, 255, 255))

    assert alpha_bbox(image) == (2, 3, 3, 4)


def test_checkerboard_uses_requested_size() -> None:
    board = checkerboard((16, 8), tile_size=4)

    assert board.size == (16, 8)
    assert board.mode == "RGBA"


def test_alpha_matte_uses_alpha_as_grayscale() -> None:
    image = Image.new("RGBA", (2, 1), (10, 20, 30, 0))
    image.putpixel((1, 0), (10, 20, 30, 200))

    matte = alpha_matte(image)

    assert matte.getpixel((0, 0)) == (0, 0, 0, 255)
    assert matte.getpixel((1, 0)) == (200, 200, 200, 255)


def test_render_preview_can_draw_bounds() -> None:
    image = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    image.putpixel((2, 3), (255, 255, 255, 255))

    result = render_preview(image, mode="bounds")

    assert result.mode == "bounds"
    assert result.alpha_bbox == (2, 3, 3, 4)
    assert result.image.size == (8, 8)
