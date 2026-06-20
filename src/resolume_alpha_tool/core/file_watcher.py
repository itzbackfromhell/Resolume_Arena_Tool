"""Simple polling watch-folder processor."""

from __future__ import annotations

import time
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

from .batch import process_files
from .models import BatchSummary, ProcessingOptions
from .validation import SUPPORTED_IMAGE_EXTENSIONS, ensure_dir

ProgressCallback = Callable[[str], None]
StopCallback = Callable[[], bool]


def _scan_current_files(input_dir: Path) -> dict[Path, float]:
    current: dict[Path, float] = {}
    for child in sorted(input_dir.iterdir()):
        if child.is_file() and child.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            with suppress(FileNotFoundError):
                current[child] = child.stat().st_mtime
    return current


def watch_folder(
    input_dir: Path,
    output_dir: Path,
    options: ProcessingOptions,
    *,
    interval_seconds: float = 2.0,
    on_progress: ProgressCallback | None = None,
    stop_after_cycles: int | None = None,
    should_stop: StopCallback | None = None,
) -> None:
    """Poll a folder and process new/changed files.

    This intentionally avoids a hard dependency on watchdog. The GUI/CLI can use
    this immediately; later versions may add native filesystem events.
    """

    source = ensure_dir(input_dir)
    seen: dict[Path, float] = {}
    cycles = 0
    while True:
        if should_stop and should_stop():
            return

        current = _scan_current_files(source)
        changed = [path for path, mtime in current.items() if seen.get(path) != mtime]
        if changed:
            summary: BatchSummary = process_files(
                changed,
                output_dir,
                options,
                on_progress=on_progress,
                should_cancel=should_stop,
            )
            for result in summary.results:
                with suppress(FileNotFoundError):
                    seen[result.input_path] = result.input_path.stat().st_mtime
            for skipped in changed:
                seen.setdefault(skipped, current[skipped])
        else:
            seen.update(current)

        cycles += 1
        if stop_after_cycles is not None and cycles >= stop_after_cycles:
            return
        time.sleep(max(0.25, interval_seconds))
