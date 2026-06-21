"""Actionable user-facing error formatting helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .exceptions import (
    AlphaDropperError,
    DependencyMissingError,
    ProcessingError,
    ResolumeApiError,
    ValidationError,
)


@dataclass(frozen=True)
class UserFacingError:
    """Normalized error payload for CLI and GUI surfaces."""

    title: str
    summary: str
    recovery_hint: str
    detail: str

    def as_cli_text(self, *, verbose: bool = False) -> str:
        """Return a compact stderr-safe message."""

        lines = [f"ERROR: {self.summary}", f"HINT: {self.recovery_hint}"]
        if verbose:
            lines.append(f"DETAIL: {self.detail}")
        return "\n".join(lines)

    def as_gui_text(self, *, verbose: bool = False) -> str:
        """Return a readable message suitable for labels and message boxes."""

        lines = [self.summary, "", f"What to try: {self.recovery_hint}"]
        if verbose:
            lines.extend(["", f"Debug detail: {self.detail}"])
        return "\n".join(lines)


def _clean_message(exc: BaseException) -> str:
    message = str(exc).strip()
    return message or exc.__class__.__name__


def build_user_error(exc: BaseException) -> UserFacingError:
    """Convert an exception into a stable, actionable user-facing error."""

    summary = _clean_message(exc)
    detail = f"{exc.__class__.__name__}: {summary}"

    if isinstance(exc, FileNotFoundError):
        return UserFacingError(
            title="Missing file",
            summary=summary,
            recovery_hint="Check the path, remove quotes/spaces copied from Explorer, and choose an existing image or folder.",
            detail=detail,
        )
    if isinstance(exc, PermissionError):
        return UserFacingError(
            title="Permission denied",
            summary=summary,
            recovery_hint="Pick a writable output folder or close apps that may be locking the file.",
            detail=detail,
        )
    if isinstance(exc, DependencyMissingError):
        return UserFacingError(
            title="Missing dependency",
            summary=summary,
            recovery_hint="Install the rembg extra and run `python -m resolume_alpha_tool.cli rembg-check` before exporting.",
            detail=detail,
        )
    if isinstance(exc, ProcessingError):
        return UserFacingError(
            title="Processing failed",
            summary=summary,
            recovery_hint="Try another supported image, verify rembg with `rembg-check`, or rerun with `--verbose` for debug detail.",
            detail=detail,
        )
    if isinstance(exc, ValidationError):
        return UserFacingError(
            title="Invalid input",
            summary=summary,
            recovery_hint="Review the selected file, output folder, target mode, preset, and overwrite settings.",
            detail=detail,
        )
    if isinstance(exc, ResolumeApiError):
        return UserFacingError(
            title="Resolume workflow failed",
            summary=summary,
            recovery_hint="Keep Resolume integration optional and export assets to a normal folder first.",
            detail=detail,
        )
    if isinstance(exc, AlphaDropperError):
        return UserFacingError(
            title="Export failed",
            summary=summary,
            recovery_hint="Check the selected inputs and rerun the command with `--verbose` if the cause is unclear.",
            detail=detail,
        )
    if isinstance(exc, ValueError):
        return UserFacingError(
            title="Invalid value",
            summary=summary,
            recovery_hint="Check the command options or GUI fields and use one of the documented supported values.",
            detail=detail,
        )
    if isinstance(exc, OSError):
        return UserFacingError(
            title="File system error",
            summary=summary,
            recovery_hint="Check that the input exists, the output folder is writable, and no file is locked by another app.",
            detail=detail,
        )
    return UserFacingError(
        title="Unexpected error",
        summary=summary,
        recovery_hint="Rerun with `--verbose` and keep the log file for debugging.",
        detail=detail,
    )
