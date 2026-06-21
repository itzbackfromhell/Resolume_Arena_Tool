"""Batch export helpers for VJ asset folders."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from .input_resolver import SUPPORTED_IMAGE_SUFFIXES
from .models import ExportTarget, ProcessingOptions, ProcessResult
from .resolume_export import DEFAULT_REMBG_MODEL, export_alpha_image, normalize_export_target

ProgressCallback = Callable[[str], None]


@dataclass(frozen=True)
class BatchExportRequest:
    """One folder-based export request."""

    input_dir: Path
    output_dir: Path
    targets: tuple[ExportTarget, ...] = ("resolume",)
    model: str = DEFAULT_REMBG_MODEL
    recursive: bool = False
    options_by_target: dict[ExportTarget, ProcessingOptions] = field(default_factory=dict)


@dataclass(frozen=True)
class BatchExportItem:
    """Result for one input/target pair, including failures without aborting the batch."""

    input_path: Path
    target: ExportTarget
    result: ProcessResult | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.result is not None and self.error is None


@dataclass(frozen=True)
class BatchExportSummary:
    """Final folder export summary."""

    input_dir: Path
    output_dir: Path
    items: tuple[BatchExportItem, ...] = field(default_factory=tuple)

    @property
    def exported_count(self) -> int:
        return sum(1 for item in self.items if item.ok)

    @property
    def failed_count(self) -> int:
        return sum(1 for item in self.items if not item.ok)

    @property
    def total_count(self) -> int:
        return len(self.items)


def normalize_batch_targets(values: Iterable[str]) -> tuple[ExportTarget, ...]:
    """Normalize user-facing target labels while preserving order and uniqueness."""

    targets: list[ExportTarget] = []
    for value in values:
        target = normalize_export_target(value)
        if target not in targets:
            targets.append(target)
    if not targets:
        raise ValueError("Select at least one export target for batch export.")
    return tuple(targets)


def discover_images(input_dir: Path, *, recursive: bool = False) -> tuple[Path, ...]:
    """Return supported image files in stable name order."""

    root = input_dir.expanduser()
    if not root.exists():
        raise FileNotFoundError(f"Batch input folder does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Batch input path is not a folder: {root}")

    iterator = root.rglob("*") if recursive else root.iterdir()
    images = [
        path
        for path in iterator
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
    ]
    return tuple(sorted(images, key=lambda path: path.name.lower()))


def export_batch(
    request: BatchExportRequest,
    *,
    on_progress: ProgressCallback | None = None,
) -> BatchExportSummary:
    """Export every supported image in a folder, collecting per-file failures."""

    sources = discover_images(request.input_dir, recursive=request.recursive)
    items: list[BatchExportItem] = []
    total_jobs = len(sources) * len(request.targets)
    completed_jobs = 0

    if on_progress:
        on_progress(f"Found {len(sources)} supported image(s). Starting {total_jobs} export job(s).")

    for source in sources:
        for target in request.targets:
            completed_jobs += 1
            if on_progress:
                on_progress(f"[{completed_jobs}/{total_jobs}] {source.name} -> {target}")
            try:
                result = export_alpha_image(
                    source,
                    request.output_dir,
                    target=target,
                    model=request.model,
                    options=request.options_by_target.get(target),
                    on_progress=on_progress,
                )
                items.append(BatchExportItem(input_path=source, target=target, result=result))
            except Exception as exc:
                items.append(BatchExportItem(input_path=source, target=target, error=str(exc)))
                if on_progress:
                    on_progress(f"Failed {source.name} ({target}): {exc}")

    return BatchExportSummary(
        input_dir=request.input_dir,
        output_dir=request.output_dir,
        items=tuple(items),
    )
