"""Batch processing service."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from .alpha_processor import process_file
from .batch_queue import canonical_output_path, scan_input_images
from .models import BatchSummary, ProcessingOptions, ProcessResult
from .naming import build_output_path
from .validation import ensure_dir, ensure_file

ProgressCallback = Callable[[str], None]
CancelCallback = Callable[[], bool]


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


def process_files(
    input_paths: Iterable[Path],
    output_dir: Path,
    options: ProcessingOptions,
    *,
    on_progress: ProgressCallback | None = None,
    should_cancel: CancelCallback | None = None,
) -> BatchSummary:
    """Process an explicit list of input files into one output directory."""

    target = ensure_dir(output_dir, create=True)
    images = [ensure_file(path) for path in input_paths]
    results: list[ProcessResult] = []
    errors: list[str] = []
    skipped = 0

    for index, image_path in enumerate(images):
        if should_cancel and should_cancel():
            remaining = len(images) - index
            skipped += remaining
            if on_progress:
                on_progress(f"CANCELLED batch export; skipped remaining={remaining}")
            break
        try:
            canonical = canonical_output_path(image_path, target, options)
            if canonical.exists() and not options.overwrite:
                skipped += 1
                if on_progress:
                    on_progress(f"Skipped existing {canonical.name}")
                continue
            output_path = build_output_path(
                image_path,
                target,
                suffix=options.normalized_suffix(),
                extension=options.output_format,
                overwrite=options.overwrite,
            )
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


def process_directory(
    input_dir: Path,
    output_dir: Path,
    options: ProcessingOptions,
    *,
    recursive: bool = False,
    on_progress: ProgressCallback | None = None,
    should_cancel: CancelCallback | None = None,
) -> BatchSummary:
    source = ensure_dir(input_dir)
    images = scan_input_images(source, mode="batch", recursive=recursive)
    return process_files(
        images,
        output_dir,
        options,
        on_progress=on_progress,
        should_cancel=should_cancel,
    )
