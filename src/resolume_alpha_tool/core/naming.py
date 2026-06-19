"""Export filename helpers."""

from __future__ import annotations

from pathlib import Path


def build_output_path(
    input_path: Path,
    output_dir: Path,
    *,
    suffix: str = "_alpha",
    extension: str = "png",
    overwrite: bool = False,
) -> Path:
    """Build a collision-safe output filename for an input image."""

    clean_ext = extension.lower().lstrip(".")
    base = f"{input_path.stem}{suffix}.{clean_ext}"
    candidate = output_dir / base
    if overwrite or not candidate.exists():
        return candidate

    index = 2
    while True:
        candidate = output_dir / f"{input_path.stem}{suffix}_{index}.{clean_ext}"
        if not candidate.exists():
            return candidate
        index += 1
