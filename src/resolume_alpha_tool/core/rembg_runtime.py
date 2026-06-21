"""Diagnostics for the optional rembg background-removal backend."""

from __future__ import annotations

import sys
import sysconfig
from importlib import metadata
from typing import Any

from PIL import Image

from .exceptions import DependencyMissingError, ProcessingError

REMBG_INSTALL_HINT = (
    'Install/test with a standard CPython x64 interpreter: python -m pip install -e ".[rembg]". '
    "Do not use the free-threaded Windows build such as Python 3.14t for rembg/onnxruntime."
)
_FALSE_CONFIG_VALUES = {"", "0", "false", "no", "off", "none"}


def package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed"


def is_free_threaded_python() -> bool:
    """Return True when running on a free-threaded CPython build."""

    gil_disabled = sysconfig.get_config_var("Py_GIL_DISABLED")
    if gil_disabled is None:
        return False
    if isinstance(gil_disabled, str):
        return gil_disabled.strip().lower() not in _FALSE_CONFIG_VALUES
    return bool(gil_disabled)


def python_abi_note() -> str:
    if is_free_threaded_python():
        return "free-threaded/3.14t ABI detected; use standard CPython x64 for rembg"
    return "standard CPython ABI"


def runtime_summary() -> str:
    return (
        f"python={sys.version.split()[0]}, "
        f"abi={python_abi_note()}, "
        f"rembg={package_version('rembg')}, "
        f"onnxruntime={package_version('onnxruntime')}, "
        f"pillow={package_version('Pillow')}"
    )


def import_rembg_symbols() -> tuple[Any, Any]:
    if is_free_threaded_python():
        raise DependencyMissingError(
            "rembg/onnxruntime is not supported by this Windows free-threaded Python build. "
            f"{REMBG_INSTALL_HINT}. Runtime: {runtime_summary()}"
        )
    try:
        from rembg import new_session, remove  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency path
        raise DependencyMissingError(
            "rembg backend could not be imported. "
            f"{REMBG_INSTALL_HINT}. Runtime: {runtime_summary()}. Original error: {exc}"
        ) from exc
    return new_session, remove


def create_rembg_session(model_name: str) -> Any:
    new_session, _remove = import_rembg_symbols()
    try:
        return new_session(model_name)
    except Exception as exc:  # pragma: no cover - depends on local model/runtime state
        raise ProcessingError(
            "rembg backend is installed but could not create a model session. "
            "This usually means the model download/cache or onnxruntime backend failed. "
            f"Model: {model_name}. Runtime: {runtime_summary()}. Original error: {exc}"
        ) from exc


def _build_healthcheck_probe_image() -> Image.Image:
    """Create a tiny synthetic foreground/background image for backend smoke tests."""

    image = Image.new("RGBA", (32, 32), (255, 255, 255, 255))
    for y in range(8, 24):
        for x in range(8, 24):
            image.putpixel((x, y), (20, 20, 20, 255))
    return image


def rembg_healthcheck(model_name: str = "u2net") -> str:
    """Import rembg, create a model session, and run one tiny removal probe."""

    session = create_rembg_session(model_name)
    _new_session, remove = import_rembg_symbols()
    probe = _build_healthcheck_probe_image()

    try:
        output = remove(probe, session=session)
    except Exception as exc:  # pragma: no cover - depends on local model/runtime state
        raise ProcessingError(
            "rembg backend imported and the model session was created, but a test removal failed. "
            f"Model: {model_name}. Runtime: {runtime_summary()}. Original error: {exc}"
        ) from exc

    if not isinstance(output, Image.Image):  # pragma: no cover - defensive guard
        raise ProcessingError(f"rembg test removal returned an unexpected output type: {type(output)!r}")
    if "A" not in output.getbands():
        raise ProcessingError("rembg test removal did not return an image with an alpha channel.")

    return (
        f"rembg ok. Model session created and test removal completed for '{model_name}'. "
        f"Runtime: {runtime_summary()}"
    )
