"""Command-line interface for Resolume Alpha Dropper."""

from __future__ import annotations

import argparse
from pathlib import Path

from .core.batch import process_directory, process_single
from .core.file_watcher import watch_folder
from .core.models import ProcessingOptions, ResolumeConfig
from .core.naming import build_output_path
from .core.presets import load_presets, options_from_preset
from .core.rembg_runtime import rembg_healthcheck, runtime_summary
from .core.resolume_api import ResolumeClient

DEFAULT_PRESET_PATH = Path(__file__).resolve().parents[2] / "presets" / "defaults.json"


def _add_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--remove-bg", action="store_true", help="Use local rembg backend.")
    parser.add_argument("--model", default="u2net", help="rembg model name.")
    parser.add_argument("--preset", help="Preset name from presets/defaults.json.")
    parser.add_argument("--alpha-threshold", type=int, default=None)
    parser.add_argument("--feather", type=float, default=None)
    parser.add_argument("--gamma", type=float, default=None)
    parser.add_argument("--despill", type=float, default=None)
    parser.add_argument("--fit", choices=["none", "contain", "cover", "stretch"], default=None)
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--format", choices=["png", "webp"], default=None)
    parser.add_argument("--suffix", default=None)
    parser.add_argument("--overwrite", action="store_true")


def _build_options(args: argparse.Namespace) -> ProcessingOptions:
    options = ProcessingOptions()
    if getattr(args, "preset", None):
        presets = load_presets(DEFAULT_PRESET_PATH)
        if args.preset not in presets:
            raise SystemExit(f"Unknown preset '{args.preset}'. Available: {', '.join(presets)}")
        options = options_from_preset(presets[args.preset], options)

    updates = {
        "remove_background": args.remove_bg or options.remove_background,
        "rembg_model": args.model or options.rembg_model,
        "alpha_threshold": args.alpha_threshold if args.alpha_threshold is not None else options.alpha_threshold,
        "feather_radius": args.feather if args.feather is not None else options.feather_radius,
        "alpha_gamma": args.gamma if args.gamma is not None else options.alpha_gamma,
        "despill_strength": args.despill if args.despill is not None else options.despill_strength,
        "fit_mode": args.fit if args.fit is not None else options.fit_mode,
        "canvas_width": args.width if args.width is not None else options.canvas_width,
        "canvas_height": args.height if args.height is not None else options.canvas_height,
        "output_format": args.format if args.format is not None else options.output_format,
        "suffix": args.suffix if args.suffix is not None else options.suffix,
        "overwrite": args.overwrite or options.overwrite,
    }
    return ProcessingOptions(**updates)


def cmd_remove(args: argparse.Namespace) -> int:
    options = _build_options(args)
    input_path = Path(args.input)
    output = Path(args.output)
    if output.suffix:
        output_path = output
    else:
        output_path = build_output_path(
            input_path,
            output,
            suffix=options.normalized_suffix(),
            extension=options.output_format,
            overwrite=options.overwrite,
        )
    result = process_single(input_path, output_path, options, on_progress=print)
    print(f"DONE {result.output_path} ({result.width}x{result.height})")
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    options = _build_options(args)
    summary = process_directory(
        Path(args.input_dir),
        Path(args.output_dir),
        options,
        recursive=args.recursive,
        on_progress=print,
    )
    print(f"DONE processed={summary.processed} failed={summary.failed} skipped={summary.skipped}")
    if summary.errors:
        print("Errors:")
        for error in summary.errors:
            print(f"- {error}")
    return 1 if summary.failed else 0


def cmd_watch(args: argparse.Namespace) -> int:
    options = _build_options(args)
    print("Watching. Press Ctrl+C to stop.")
    try:
        watch_folder(
            Path(args.input_dir),
            Path(args.output_dir),
            options,
            interval_seconds=args.interval,
            on_progress=print,
        )
    except KeyboardInterrupt:
        print("Stopped.")
    return 0


def cmd_resolume(args: argparse.Namespace) -> int:
    client = ResolumeClient(ResolumeConfig(host=args.host, port=args.port, timeout_seconds=args.timeout))
    ok = client.healthcheck()
    print("Resolume webserver reachable." if ok else "Resolume webserver not reachable.")
    return 0 if ok else 1


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

    remove = sub.add_parser("remove", help="Process a single image.")
    remove.add_argument("input")
    remove.add_argument("output", help="Output file or output directory.")
    _add_options(remove)
    remove.set_defaults(func=cmd_remove)

    batch = sub.add_parser("batch", help="Process a folder.")
    batch.add_argument("input_dir")
    batch.add_argument("output_dir")
    batch.add_argument("--recursive", action="store_true")
    _add_options(batch)
    batch.set_defaults(func=cmd_batch)

    watch = sub.add_parser("watch", help="Watch a folder and process images repeatedly.")
    watch.add_argument("input_dir")
    watch.add_argument("output_dir")
    watch.add_argument("--interval", type=float, default=2.0)
    _add_options(watch)
    watch.set_defaults(func=cmd_watch)

    rembg = sub.add_parser("rembg-check", help="Test optional rembg backend and model session.")
    rembg.add_argument("--model", default="u2net")
    rembg.set_defaults(func=cmd_rembg_check)

    resolume = sub.add_parser("resolume", help="Test local Resolume webserver connectivity.")
    resolume.add_argument("--host", default="127.0.0.1")
    resolume.add_argument("--port", type=int, default=8080)
    resolume.add_argument("--timeout", type=float, default=2.0)
    resolume.set_defaults(func=cmd_resolume)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
