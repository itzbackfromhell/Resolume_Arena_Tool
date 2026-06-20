from PIL import Image

from resolume_alpha_tool.core.alpha_processor import process_image_object
from resolume_alpha_tool.core.models import ProcessingOptions


def _visible_pixel_count(image: Image.Image) -> int:
    histogram = image.getchannel("A").histogram()
    return sum(histogram[1:])


def test_auto_crop_with_padding_trims_transparent_bounds() -> None:
    image = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    image.paste((255, 0, 0, 255), (4, 4, 6, 6))

    processed = process_image_object(
        image,
        ProcessingOptions(
            alpha_threshold=0,
            feather_radius=0,
            despill_strength=0,
            auto_crop=True,
            padding=1,
        ),
    )

    assert processed.size == (4, 4)


def test_outline_adds_visible_pixels_around_alpha() -> None:
    image = Image.new("RGBA", (9, 9), (0, 0, 0, 0))
    image.paste((255, 0, 0, 255), (3, 3, 6, 6))

    plain = process_image_object(
        image,
        ProcessingOptions(alpha_threshold=0, feather_radius=0, despill_strength=0, auto_crop=True),
    )
    outlined = process_image_object(
        image,
        ProcessingOptions(
            alpha_threshold=0,
            feather_radius=0,
            despill_strength=0,
            auto_crop=True,
            outline_width=1,
        ),
    )

    assert outlined.getchannel("A").getbbox() is not None
    assert _visible_pixel_count(outlined) > _visible_pixel_count(plain)


def test_invert_alpha_flips_mask() -> None:
    image = Image.new("RGBA", (2, 1), (255, 0, 0, 0))
    image.putpixel((0, 0), (255, 0, 0, 255))

    processed = process_image_object(
        image,
        ProcessingOptions(alpha_threshold=0, feather_radius=0, despill_strength=0, invert_alpha=True),
    )

    assert processed.getpixel((0, 0))[3] == 0
    assert processed.getpixel((1, 0))[3] == 255
