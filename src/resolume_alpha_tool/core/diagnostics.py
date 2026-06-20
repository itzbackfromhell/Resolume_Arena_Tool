"""Runtime diagnostics for support and portable releases."""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime
from importlib import metadata
from pathlib import Path
from typing import Any

from .resources import default_preset_path, portable_log_dir, portable_output_dir, portable_root


def _version(package: str) -> str | None:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def build_diagnostics_payload() -> dict[str, Any]:
    """Return a JSON-serializable diagnostics snapshot."""

    preset_path = default_preset_path()
    output_dir = portable_output_dir()
    log_dir = portable_log_dir()
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "app": {
            "name": "Resolume Alpha Dropper",
            "package_version": _version("resolume-alpha-dropper"),
            "portable_root": str(portable_root()),
        },
        "python": {
            "executable": sys.executable,
            "version": sys.version,
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "packages": {
            "Pillow": _version("Pillow"),
            "requests": _version("requests"),
            "rembg": _version("rembg"),
            "onnxruntime": _version("onnxruntime"),
            "pyinstaller": _version("pyinstaller"),
        },
        "paths": {
            "default_preset_path": str(preset_path),
            "default_preset_exists": preset_path.exists(),
            "output_dir": str(output_dir),
            "output_dir_exists": output_dir.exists(),
            "log_dir": str(log_dir),
            "log_dir_exists": log_dir.exists(),
        },
    }


def default_diagnostics_path() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return portable_log_dir() / f"diagnostic_{stamp}.json"


def write_diagnostics_report(path: Path | None = None) -> Path:
    """Write a diagnostics report and return its path."""

    report_path = path or default_diagnostics_path()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(build_diagnostics_payload(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return report_path
