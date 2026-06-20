"""Export report helpers."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import BatchSummary, ProcessingOptions


def _options_payload(options: ProcessingOptions) -> dict[str, Any]:
    return asdict(options)


def _result_payload(result) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    return {
        "input_path": str(result.input_path),
        "output_path": str(result.output_path),
        "width": result.width,
        "height": result.height,
        "had_alpha": result.had_alpha,
        "background_removed": result.background_removed,
        "warnings": list(result.warnings),
    }


def build_report_payload(
    *,
    mode: str,
    input_path: Path,
    output_dir: Path,
    options: ProcessingOptions,
    summary: BatchSummary,
    skipped_existing: list[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build a JSON-serializable export report payload."""

    return {
        "created_at": datetime.now(UTC).isoformat(),
        "mode": mode,
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "options": _options_payload(options),
        "summary": {
            "processed": summary.processed,
            "failed": summary.failed,
            "skipped": summary.skipped,
        },
        "results": [_result_payload(result) for result in summary.results],
        "errors": list(summary.errors),
        "skipped_existing": list(skipped_existing),
    }


def write_export_report(
    *,
    report_path: Path,
    mode: str,
    input_path: Path,
    output_dir: Path,
    options: ProcessingOptions,
    summary: BatchSummary,
    skipped_existing: list[str] | tuple[str, ...] = (),
) -> Path:
    """Write a machine-readable JSON export report."""

    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_report_payload(
        mode=mode,
        input_path=input_path,
        output_dir=output_dir,
        options=options,
        summary=summary,
        skipped_existing=skipped_existing,
    )
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return report_path


def default_report_path(output_dir: Path) -> Path:
    """Return a timestamped report filename inside the output directory."""

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"export_report_{stamp}.json"
