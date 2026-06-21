"""Diagnostics for the optional rembg background-removal backend."""

from __future__ import annotations

import sys
import sysconfig
from importlib import metadata
from typing import Any

from .exceptions import DependencyMissingError, ProcessingError

REMBG_INSTALL_HINT = (
    'Install/test with a standard CPython x64 interpreter: python -m pip install -e ".[rembg]". '
    "Do not use the free-threaded Windows build such as Python 3.14t for rembg/onnxruntime."
)


def package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed"


def is_free_threaded_python() -> bool:
    """Return True when running on a free-threaded CPython build."""

    gil_disabled = sysconfig.get_config_var("Py_GIL_DISABLED")
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


def rembg_healthcheck(model_name: str = "u2net") -> str:
    """Import rembg and create a model session, returning a human-readable status."""

    create_rembg_session(model_name)
    return f"rembg ok. Model session created for '{model_name}'. Runtime: {runtime_summary()}"
