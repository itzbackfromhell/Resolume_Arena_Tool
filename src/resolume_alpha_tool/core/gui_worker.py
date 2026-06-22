"""Thread-safe GUI worker message helpers.

The Tkinter app can only update widgets on the main thread. This module keeps
worker communication explicit and testable: background threads emit small
message objects into a queue, and the UI decides how to render them.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, Protocol, TypeVar

from .error_ux import UserFacingError, build_user_error

GuiWorkerMessageKind = Literal[
    "progress",
    "export_success",
    "batch_success",
    "export_error",
    "export_finished",
]

T = TypeVar("T")


class MessageSink(Protocol):
    """Minimal queue-compatible sink used by worker threads."""

    def put(self, item: object) -> None:
        """Add one item to the sink."""


@dataclass(frozen=True)
class GuiWorkerMessage:
    """Single message passed from worker threads to the Tk main thread."""

    kind: GuiWorkerMessageKind
    payload: object = None


def make_progress_message(text: object) -> GuiWorkerMessage:
    """Build a progress message with safe string payload."""

    return GuiWorkerMessage("progress", str(text))


def make_success_message(kind: Literal["export_success", "batch_success"], payload: object) -> GuiWorkerMessage:
    """Build a typed success message."""

    return GuiWorkerMessage(kind, payload)


def make_error_message(exc: BaseException) -> GuiWorkerMessage:
    """Build a user-facing error message from an exception."""

    return GuiWorkerMessage("export_error", build_user_error(exc))


def make_finished_message() -> GuiWorkerMessage:
    """Build the final worker lifecycle message."""

    return GuiWorkerMessage("export_finished")


def coerce_worker_message(item: object) -> GuiWorkerMessage | None:
    """Accept the new dataclass and legacy ``(kind, payload)`` tuples.

    Legacy tuple support keeps the current GUI queue drain compatible while the
    app is gradually refactored into smaller UI modules.
    """

    if isinstance(item, GuiWorkerMessage):
        return item
    if isinstance(item, tuple) and len(item) == 2:
        kind, payload = item
        if kind in GuiWorkerMessage.__annotations__.get("kind", ()):
            return GuiWorkerMessage(kind, payload)
        if isinstance(kind, str) and kind in {
            "progress",
            "export_success",
            "batch_success",
            "export_error",
            "export_finished",
        }:
            return GuiWorkerMessage(kind, payload)
    return None


def put_progress(sink: MessageSink, text: object) -> None:
    """Put one progress message into a queue-compatible sink."""

    sink.put(make_progress_message(text))


def run_worker_task(
    *,
    sink: MessageSink,
    task: Callable[[], T],
    success_kind: Literal["export_success", "batch_success"],
    logger: logging.Logger | None = None,
) -> None:
    """Run a worker task and always emit success/error plus finished.

    This function is intentionally small and synchronous so it can be used as a
    ``threading.Thread`` target and tested without starting real threads.
    """

    try:
        result = task()
    except Exception as exc:  # noqa: BLE001 - GUI worker boundary must catch all export failures.
        if logger is not None:
            logger.exception("GUI worker task failed")
        sink.put(make_error_message(exc))
    else:
        sink.put(make_success_message(success_kind, result))
    finally:
        sink.put(make_finished_message())


def user_error_from_payload(payload: object) -> UserFacingError:
    """Normalize queue error payloads from new or legacy workers."""

    if isinstance(payload, UserFacingError):
        return payload
    if isinstance(payload, BaseException):
        return build_user_error(payload)
    return build_user_error(RuntimeError(str(payload)))


def message_payload_text(payload: Any) -> str:
    """Return a safe one-line-ish string for GUI labels."""

    if isinstance(payload, UserFacingError):
        return payload.as_gui_text()
    return str(payload)
