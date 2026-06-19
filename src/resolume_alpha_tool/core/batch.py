"""Batch processing service."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .alpha_processor import process_file
from .models import BatchSummary, ProcessingOptions, ProcessResult
from .naming import build_output_path
from .validation import ensure_dir, ensure_file, iter_images

ProgressCallback = Callable[[str], None]


def process_single(
    input_path: Path,
    output_path: Path,
    options: ProcessingOptions,
    *,
    on_progress: ProgressCallback | None = None,
) -> ProcessResult:
    input_file = ensure_file(input_path)
    if on_progress:
        on_progress(f"Processing {input_file.name}")
    result = process_file(input_file, output_path, options)
    if on_progress:
        on_progress(f"Saved {result.output_path.name}")
    return result


def process_directory(
    input_dir: Path,
    output_dir: Path,
    options: ProcessingOptions,
    *,
    recursive: bool = False,
    on_progress: ProgressCallback | None = None,
) -> BatchSummary:
    source = ensure_dir(input_dir)
    target = ensure_dir(output_dir, create=True)

    if recursive:
        from .validation import SUPPORTED_IMAGE_EXTENSIONS

        images = sorted(
            child
            for child in source.rglob("*")
            if child.is_file() and child.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        )
    else:
        images = iter_images(source)

    results: list[ProcessResult] = []
    errors: list[str] = []
    skipped = 0

    for image_path in images:
        try:
            output_path = build_output_path(
                image_path,
                target,
                suffix=options.normalized_suffix(),
                extension=options.output_format,
                overwrite=options.overwrite,
            )
            if output_path.exists() and not options.overwrite:
                skipped += 1
                continue
            if on_progress:
                on_progress(f"Processing {image_path.name}")
            result = process_file(image_path, output_path, options)
            results.append(result)
            if on_progress:
                on_progress(f"Saved {result.output_path.name}")
        except Exception as exc:  # continue batch runs; collect errors
            errors.append(f"{image_path}: {exc}")
            if on_progress:
                on_progress(f"ERROR {image_path.name}: {exc}")

    return BatchSummary(
        processed=len(results),
        failed=len(errors),
        skipped=skipped,
        results=tuple(results),
        errors=tuple(errors),
    )
