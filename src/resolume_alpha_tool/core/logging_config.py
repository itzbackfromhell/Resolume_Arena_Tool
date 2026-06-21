"""Logging setup for CLI and desktop workflows."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from .gui_settings import config_dir

LOGGER_NAME = "resolume_alpha_tool"
LOG_FILE_NAME = "alpha_png_exporter.log"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_CONFIGURED_MARKER = "_alpha_png_exporter_handler"


def log_file_path() -> Path:
    """Return the per-user log file path."""

    return config_dir() / LOG_FILE_NAME


def _mark_handler(handler: logging.Handler) -> logging.Handler:
    setattr(handler, _CONFIGURED_MARKER, True)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    return handler


def configure_logging(*, verbose: bool = False, log_to_file: bool = True) -> logging.Logger:
    """Configure the package logger once and return it.

    Normal CLI output stays clean by default: logs go to the per-user log file.
    With ``verbose=True`` a stderr handler is also enabled for immediate debug detail.
    """

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.propagate = False

    for handler in list(logger.handlers):
        if getattr(handler, _CONFIGURED_MARKER, False):
            logger.removeHandler(handler)
            handler.close()

    configured_handlers: list[logging.Handler] = []
    if log_to_file:
        try:
            path = log_file_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            configured_handlers.append(_mark_handler(logging.FileHandler(path, encoding="utf-8")))
        except OSError:
            # Logging must never break exports. If the config dir is unavailable,
            # keep running and fall back to stderr only when verbose is requested.
            configured_handlers = []

    if verbose:
        configured_handlers.append(_mark_handler(logging.StreamHandler(sys.stderr)))

    if not configured_handlers:
        configured_handlers.append(_mark_handler(logging.NullHandler()))

    for handler in configured_handlers:
        handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        logger.addHandler(handler)

    return logger
