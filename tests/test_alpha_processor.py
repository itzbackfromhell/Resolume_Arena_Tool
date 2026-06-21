from pathlib import Path

from PIL import Image

from resolume_alpha_tool.core.alpha_processor import process_file, process_image_object
from resolume_alpha_tool.core.models import ProcessingOptions


def test_process_image_thresholds_alpha() -> None:
    img = Image.new("RGBA", (2, 1), (255, 255, 255, 255))
    img.putpixel((0, 0), (255, 255, 255, 3))
    out = process_image_object(
        img,
        ProcessingOptions(
            remove_background=False,
            alpha_threshold=8,
            feather_radius=0,
            despill_strength=0,
        ),
    )
    assert out.getpixel((0, 0))[3] == 0
    assert out.getpixel((1, 0))[3] == 255


def test_process_image_erodes_alpha_edge() -> None:
    img = Image.new("RGBA", (5, 5), (255, 255, 255, 0))
    for y in range(1, 4):
        for x in range(1, 4):
            img.putpixel((x, y), (255, 255, 255, 255))

    out = process_image_object(
        img,
        ProcessingOptions(
            remove_background=False,
            alpha_threshold=0,
            feather_radius=0,
            despill_strength=0,
            alpha_erode=1,
        ),
    )

    assert out.getpixel((1, 1))[3] == 0
    assert out.getpixel((2, 2))[3] == 255


def test_process_image_dilates_alpha_edge(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    matte = Image.new("RGBA", (5, 5), (255, 255, 255, 0))
    matte.putpixel((2, 2), (255, 255, 255, 255))
    img = Image.new("RGB", (5, 5), (255, 255, 255))

    monkeypatch.setattr(
        "resolume_alpha_tool.core.alpha_processor._remove_background_with_rembg",
        lambda _image, _model: matte,
    )

    out = process_image_object(
        img,
        ProcessingOptions(
            remove_background=True,
            alpha_threshold=0,
            feather_radius=0,
            despill_strength=0,
            alpha_dilate=1,
        ),
    )

    assert out.getpixel((1, 2))[3] == 255
    assert out.getpixel((2, 2))[3] == 255


def test_process_image_contain_canvas() -> None:
    img = Image.new("RGBA", (100, 50), (255, 0, 0, 255))
    out = process_image_object(
        img,
        ProcessingOptions(
            fit_mode="contain",
            canvas_width=200,
            canvas_height=200,
            feather_radius=0,
            despill_strength=0,
        ),
    )
    assert out.size == (200, 200)


def test_process_file_writes_png(tmp_path: Path) -> None:
    input_path = tmp_path / "in.png"
    output_path = tmp_path / "out.png"
    Image.new("RGBA", (8, 8), (10, 20, 30, 255)).save(input_path)
    result = process_file(
        input_path,
        output_path,
        ProcessingOptions(feather_radius=0, despill_strength=0, overwrite=True),
    )
    assert output_path.exists()
    assert result.width == 8
    assert result.height == 8
