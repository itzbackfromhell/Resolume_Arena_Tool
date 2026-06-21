"""JSON reporting helpers for export summaries."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def batch_report_payload(summary) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Return a JSON-friendly payload for a batch export summary."""

    items: list[dict[str, Any]] = []
    for item in summary.items:
        result = item.result
        items.append(
            {
                "input_path": str(item.input_path),
                "target": item.target,
                "ok": item.ok,
                "output_path": str(result.output_path) if result is not None else None,
                "width": getattr(result, "width", None) if result is not None else None,
                "height": getattr(result, "height", None) if result is not None else None,
                "error": item.error,
            }
        )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "input_dir": str(summary.input_dir),
        "output_dir": str(summary.output_dir),
        "totals": {
            "total": summary.total_count,
            "exported": summary.exported_count,
            "failed": summary.failed_count,
        },
        "items": items,
    }


def write_batch_report(summary, report_path: Path) -> Path:  # type: ignore[no-untyped-def]
    """Write a batch export JSON report and return the written path."""

    path = report_path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(batch_report_payload(summary), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path
