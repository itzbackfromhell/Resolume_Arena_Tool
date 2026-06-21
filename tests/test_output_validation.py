from pathlib import Path

import pytest
from PIL import Image

from resolume_alpha_tool.core.exceptions import ProcessingError
from resolume_alpha_tool.core.models import ProcessResult
from resolume_alpha_tool.core.output_validation import validate_output_file
from resolume_alpha_tool.core.resolume_export import resolume_processing_options, shirt_print_processing_options


def _result(path: Path, *, width: int, height: int, background_removed: bool = True) -> ProcessResult:
    return ProcessResult(
        input_path=path,
        output_path=path,
        width=width,
        height=height,
        had_alpha=True,
        background_removed=background_removed,
    )


def test_output_validation_report_includes_alpha_diagnostics(tmp_path: Path) -> None:
    path = tmp_path / "asset.png"
    image = Image.new("RGBA", (8, 8), (255, 255, 255, 255))
    image.putpixel((0, 0), (0, 0, 0, 0))
    image.save(path)

    report = validate_output_file(
        _result(path, width=8, height=8),
        shirt_print_processing_options(),
        target="shirt_print",
    )

    assert report.output_path == path
    assert report.size_label == "8x8"
    assert report.alpha_min == 0
    assert report.alpha_max == 255
    assert report.visible_percent < 100.0


def test_output_validation_rejects_wrong_resolume_size(tmp_path: Path) -> None:
    path = tmp_path / "asset.png"
    Image.new("RGBA", (8, 8), (255, 255, 255, 0)).save(path)

    with pytest.raises(ProcessingError, match="Resolume export must be 1920x1080"):
        validate_output_file(
            _result(path, width=8, height=8),
            resolume_processing_options(),
            target="resolume",
        )


def test_output_validation_can_preflight_without_background_removed_flag(tmp_path: Path) -> None:
    path = tmp_path / "asset.png"
    image = Image.new("RGBA", (8, 8), (255, 255, 255, 255))
    image.putpixel((0, 0), (0, 0, 0, 0))
    image.save(path)

    report = validate_output_file(
        _result(path, width=8, height=8, background_removed=False),
        shirt_print_processing_options(),
        target="shirt_print",
        require_background_removed=False,
    )

    assert report.alpha_min == 0


def test_output_validation_rejects_fully_opaque_alpha(tmp_path: Path) -> None:
    path = tmp_path / "opaque.png"
    Image.new("RGBA", (8, 8), (255, 255, 255, 255)).save(path)

    with pytest.raises(ProcessingError, match="fully opaque PNG"):
        validate_output_file(
            _result(path, width=8, height=8),
            shirt_print_processing_options(),
            target="shirt_print",
        )
