"""Command-line interface for focused alpha exports."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core.batch_export import BatchExportRequest, export_batch, normalize_batch_targets
from .core.exceptions import AlphaDropperError
from .core.rembg_runtime import rembg_healthcheck, runtime_summary
from .core.resolume_export import (
    CLI_TARGET_CHOICES,
    DEFAULT_REMBG_MODEL,
    export_alpha_image,
    normalize_export_target,
)


def cmd_convert(args: argparse.Namespace) -> int:
    result = export_alpha_image(
        Path(args.input),
        Path(args.output_dir),
        target=normalize_export_target(args.target),
        model=args.model,
        on_progress=print,
    )
    print(f"DONE {result.output_path} ({result.width}x{result.height})")
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    targets = normalize_batch_targets(args.target)
    summary = export_batch(
        BatchExportRequest(
            input_dir=Path(args.input_dir),
            output_dir=Path(args.output_dir),
            targets=targets,
            model=args.model,
            recursive=args.recursive,
        ),
        on_progress=print,
    )
    print(
        f"DONE batch: {summary.exported_count} exported, "
        f"{summary.failed_count} failed, {summary.total_count} total"
    )
    return 0 if summary.failed_count == 0 else 2


def cmd_rembg_check(args: argparse.Namespace) -> int:
    print(f"Runtime: {runtime_summary()}")
    try:
        print(rembg_healthcheck(args.model))
    except Exception as exc:
        print(f"rembg check failed: {exc}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="resolume-alpha")
    sub = parser.add_subparsers(dest="command", required=True)

    convert = sub.add_parser("convert", help="Convert one image into a background-removed PNG.")
    convert.add_argument("input")
    convert.add_argument("output_dir")
    convert.add_argument("--target", choices=CLI_TARGET_CHOICES, default="resolume")
    convert.add_argument("--model", default=DEFAULT_REMBG_MODEL)
    convert.set_defaults(func=cmd_convert)

    batch = sub.add_parser("batch", help="Convert every supported image in a folder.")
    batch.add_argument("input_dir")
    batch.add_argument("output_dir")
    batch.add_argument(
        "--target",
        choices=CLI_TARGET_CHOICES,
        action="append",
        default=["resolume"],
        help="Export target. Pass twice to export both modes.",
    )
    batch.add_argument("--recursive", action="store_true")
    batch.add_argument("--model", default=DEFAULT_REMBG_MODEL)
    batch.set_defaults(func=cmd_batch)

    rembg = sub.add_parser("rembg-check", help="Test required rembg backend and model session.")
    rembg.add_argument("--model", default=DEFAULT_REMBG_MODEL)
    rembg.set_defaults(func=cmd_rembg_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (AlphaDropperError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
