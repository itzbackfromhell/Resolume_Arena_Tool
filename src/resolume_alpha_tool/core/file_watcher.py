"""Simple polling watch-folder processor."""

from __future__ import annotations

import time
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

from .batch import process_directory
from .models import BatchSummary, ProcessingOptions

ProgressCallback = Callable[[str], None]


def watch_folder(
    input_dir: Path,
    output_dir: Path,
    options: ProcessingOptions,
    *,
    interval_seconds: float = 2.0,
    on_progress: ProgressCallback | None = None,
    stop_after_cycles: int | None = None,
) -> None:
    """Poll a folder and process new/changed files.

    This intentionally avoids a hard dependency on watchdog. The GUI/CLI can use
    this immediately; later versions may add native filesystem events.
    """

    seen: dict[Path, float] = {}
    cycles = 0
    while True:
        summary: BatchSummary = process_directory(
            input_dir,
            output_dir,
            options,
            recursive=False,
            on_progress=on_progress,
        )
        for result in summary.results:
            with suppress(FileNotFoundError):
                seen[result.input_path] = result.input_path.stat().st_mtime

        cycles += 1
        if stop_after_cycles is not None and cycles >= stop_after_cycles:
            return
        time.sleep(max(0.25, interval_seconds))
