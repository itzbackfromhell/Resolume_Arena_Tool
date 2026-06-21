"""Command-line interface for focused alpha exports."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from PIL import Image

from .core.batch_export import BatchExportRequest, export_batch, normalize_batch_targets
from .core.exceptions import AlphaDropperError
from .core.models import ProcessResult
from .core.output_validation import validate_output_file
from .core.rembg_runtime import rembg_healthcheck, runtime_summary
from .core.resolume_export import (
    CLI_TARGET_CHOICES,
    DEFAULT_REMBG_MODEL,
    EDGE_CLEANUP_PROFILES,
    export_alpha_image,
    normalize_export_target,
    normalize_resolume_preset,
    resolume_processing_options,
    shirt_print_processing_options,
)
from .core.validation import ensure_file

RESOLUME_PRESET_CHOICES = ("1080p", "4k", "square-1080", "square_1080")
FIT_MODE_CHOICES = ("contain", "cover", "stretch")


def _resolved_model(args: argparse.Namespace) -> str:
    return args.model if args.model is not None else DEFAULT_REMBG_MODEL


def _options_for_target(args: argparse.Namespace, target_label: str):
    target = normalize_export_target(target_label)
    model = _resolved_model(args)
    if target == "shirt_print":
        options = shirt_print_processing_options(
            model,
            padding=args.shirt_padding,
            edge_profile=args.edge_profile,
        )
    else:
        options = resolume_processing_options(
            model,
            canvas_size=normalize_resolume_preset(args.preset),
            fit_mode=args.fit,
            edge_profile=args.edge_profile,
        )
    if args.overwrite:
        options = replace(options, overwrite=True)
    return options


def _add_single_export_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", choices=CLI_TARGET_CHOICES, default="resolume")
    _add_shared_export_options(parser)


def _add_batch_export_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--target",
        choices=CLI_TARGET_CHOICES,
        action="append",
        default=None,
        help="Export target. Pass twice to export both modes. Default: resolume.",
    )
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--report", help="Write a JSON batch report to this path.")
    _add_shared_export_options(parser)


def _add_shared_export_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", default=None, help="rembg model name. Default: u2net.")
    parser.add_argument(
        "--preset",
        choices=RESOLUME_PRESET_CHOICES,
        default="1080p",
        help="Resolume canvas preset for Resolume targets.",
    )
    parser.add_argument("--fit", choices=FIT_MODE_CHOICES, default="contain", help="Resolume canvas fit mode.")
    parser.add_argument(
        "--edge-profile",
        choices=EDGE_CLEANUP_PROFILES,
        default="normal",
        help="Small safe alpha cleanup profile.",
    )
    parser.add_argument(
        "--shirt-padding",
        type=int,
        default=96,
        help="Transparent padding in pixels for shirt/print targets.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing output file.")


def cmd_convert(args: argparse.Namespace) -> int:
    target = normalize_export_target(args.target)
    options = _options_for_target(args, args.target)
    result = export_alpha_image(
        Path(args.input),
        Path(args.output_dir),
        target=target,
        model=options.rembg_model,
        options=options,
        on_progress=print,
    )
    print(f"DONE {result.output_path} ({result.width}x{result.height})")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    """Compatibility alias for older docs and muscle-memory workflows."""

    return cmd_convert(args)


def cmd_batch(args: argparse.Namespace) -> int:
    targets = normalize_batch_targets(args.target or ["resolume"])
    options_by_target = {target: _options_for_target(args, target) for target in targets}
    summary = export_batch(
        BatchExportRequest(
            input_dir=Path(args.input_dir),
            output_dir=Path(args.output_dir),
            targets=targets,
            model=_resolved_model(args),
            recursive=args.recursive,
            report_path=Path(args.report) if args.report else None,
            options_by_target=options_by_target,
        ),
        on_progress=print,
    )
    print(
        f"DONE batch: {summary.exported_count} exported, "
        f"{summary.failed_count} failed, {summary.total_count} total"
    )
    return 0 if summary.failed_count == 0 else 2


def cmd_validate(args: argparse.Namespace) -> int:
    target = normalize_export_target(args.target)
    options = _options_for_target(args, args.target)
    path = ensure_file(Path(args.input))
    with Image.open(path) as image:
        result = ProcessResult(
            input_path=path,
            output_path=path,
            width=image.width,
            height=image.height,
            had_alpha="A" in image.getbands(),
            background_removed=False,
        )
    report = validate_output_file(
        result,
        options,
        target=target,
        require_background_removed=False,
    )
    print(f"VALID {report.output_path} ({report.size_label}, {report.alpha_label})")
    for warning in report.warnings:
        print(f"WARN {warning}")
    return 0


def cmd_rembg_check(args: argparse.Namespace) -> int:
    print(f"Runtime: {runtime_summary()}")
    try:
        print(rembg_healthcheck(args.model))
    except Exception as exc:
        print(f"rembg check failed: {exc}")
        return 1
    return 0


def cmd_version(_args: argparse.Namespace) -> int:
    from resolume_alpha_tool import __version__

    print(__version__)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="resolume-alpha")
    sub = parser.add_subparsers(dest="command", required=True)

    convert = sub.add_parser("convert", help="Convert one image into a background-removed PNG.")
    convert.add_argument("input")
    convert.add_argument("output_dir")
    _add_single_export_options(convert)
    convert.set_defaults(func=cmd_convert)

    remove = sub.add_parser("remove", help="Alias for convert with the same professional export options.")
    remove.add_argument("input")
    remove.add_argument("output_dir")
    _add_single_export_options(remove)
    remove.set_defaults(func=cmd_remove)

    batch = sub.add_parser("batch", help="Convert every supported image in a folder.")
    batch.add_argument("input_dir")
    batch.add_argument("output_dir")
    _add_batch_export_options(batch)
    batch.set_defaults(func=cmd_batch)

    validate = sub.add_parser("validate", help="Validate an exported alpha PNG against a target contract.")
    validate.add_argument("input")
    validate.add_argument("--target", choices=CLI_TARGET_CHOICES, default="resolume")
    validate.add_argument("--preset", choices=RESOLUME_PRESET_CHOICES, default="1080p")
    validate.add_argument("--fit", choices=FIT_MODE_CHOICES, default="contain")
    validate.add_argument("--edge-profile", choices=EDGE_CLEANUP_PROFILES, default="normal")
    validate.add_argument("--shirt-padding", type=int, default=96)
    validate.add_argument("--model", default=None)
    validate.add_argument("--overwrite", action="store_true")
    validate.set_defaults(func=cmd_validate)

    rembg = sub.add_parser("rembg-check", help="Test required rembg backend and model session.")
    rembg.add_argument("--model", default=DEFAULT_REMBG_MODEL)
    rembg.set_defaults(func=cmd_rembg_check)

    version = sub.add_parser("version", help="Print the package version.")
    version.set_defaults(func=cmd_version)

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
