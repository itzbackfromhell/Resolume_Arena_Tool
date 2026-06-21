"""Command-line interface for the single-image Resolume export."""

from __future__ import annotations

import argparse
from pathlib import Path

from .core.rembg_runtime import rembg_healthcheck, runtime_summary
from .core.resolume_export import DEFAULT_REMBG_MODEL, export_resolume_image


def cmd_convert(args: argparse.Namespace) -> int:
    result = export_resolume_image(
        Path(args.input),
        Path(args.output_dir),
        model=args.model,
        on_progress=print,
    )
    print(f"DONE {result.output_path} ({result.width}x{result.height})")
    return 0


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

    convert = sub.add_parser("convert", help="Convert one image into a Resolume-ready PNG.")
    convert.add_argument("input")
    convert.add_argument("output_dir")
    convert.add_argument("--model", default=DEFAULT_REMBG_MODEL)
    convert.set_defaults(func=cmd_convert)

    rembg = sub.add_parser("rembg-check", help="Test optional rembg backend and model session.")
    rembg.add_argument("--model", default=DEFAULT_REMBG_MODEL)
    rembg.set_defaults(func=cmd_rembg_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
