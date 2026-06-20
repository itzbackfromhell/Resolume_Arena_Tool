"""Batch queue discovery helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .models import ProcessingOptions
from .naming import build_output_path
from .validation import SUPPORTED_IMAGE_EXTENSIONS, ensure_dir, ensure_file, iter_images

QueueStatus = Literal["pending", "skipped_existing"]


@dataclass(frozen=True)
class QueueItem:
    """One planned export item for the GUI queue."""

    input_path: Path
    output_path: Path
    status: QueueStatus = "pending"


def canonical_output_path(input_path: Path, output_dir: Path, options: ProcessingOptions) -> Path:
    """Return the non-collision output path for an input image."""

    clean_ext = options.output_format.lower().lstrip(".")
    return output_dir / f"{input_path.stem}{options.normalized_suffix()}.{clean_ext}"


def explicit_file_queue_item(
    input_path: Path,
    output_dir: Path,
    options: ProcessingOptions,
) -> QueueItem:
    """Build the preview item for one explicit-file export entry."""

    source = input_path.expanduser().resolve()
    output_path = canonical_output_path(source, output_dir, options)
    status: QueueStatus = (
        "skipped_existing" if output_path.exists() and not options.overwrite else "pending"
    )
    return QueueItem(input_path=source, output_path=output_path, status=status)


def scan_file_export_queue(
    input_paths: Iterable[Path],
    output_dir: Path,
    options: ProcessingOptions,
) -> tuple[QueueItem, ...]:
    """Build a queue preview for an explicit list of files, such as retry exports."""

    target = output_dir.expanduser().resolve()
    return tuple(explicit_file_queue_item(path, target, options) for path in input_paths)


def scan_input_images(input_path: Path, *, mode: str, recursive: bool = False) -> tuple[Path, ...]:
    """Resolve the images that a single/batch job would process."""

    if mode == "single":
        return (ensure_file(input_path),)

    source = ensure_dir(input_path)
    if recursive:
        return tuple(
            sorted(
                child
                for child in source.rglob("*")
                if child.is_file() and child.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
            )
        )
    return tuple(iter_images(source))


def scan_export_queue(
    input_path: Path,
    output_dir: Path,
    options: ProcessingOptions,
    *,
    mode: str,
    recursive: bool = False,
) -> tuple[QueueItem, ...]:
    """Build a queue preview for a future export job."""

    target = output_dir.expanduser().resolve()
    images = scan_input_images(input_path, mode=mode, recursive=recursive)
    items: list[QueueItem] = []
    for image_path in images:
        if mode == "single":
            output_path = build_output_path(
                image_path,
                target,
                suffix=options.normalized_suffix(),
                extension=options.output_format,
                overwrite=options.overwrite,
            )
            status: QueueStatus = "pending"
        else:
            output_path = canonical_output_path(image_path, target, options)
            status = "skipped_existing" if output_path.exists() and not options.overwrite else "pending"
        items.append(QueueItem(input_path=image_path, output_path=output_path, status=status))
    return tuple(items)


def failed_input_paths(errors: tuple[str, ...] | list[str]) -> tuple[Path, ...]:
    """Extract failed input paths from BatchSummary error strings."""

    paths: list[Path] = []
    for error in errors:
        path_text, _separator, _message = str(error).partition(": ")
        if path_text:
            paths.append(Path(path_text))
    return tuple(paths)
