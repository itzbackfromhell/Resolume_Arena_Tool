import logging
import queue

from resolume_alpha_tool.core.error_ux import UserFacingError
from resolume_alpha_tool.core.gui_worker import (
    GuiWorkerMessage,
    coerce_worker_message,
    make_progress_message,
    message_payload_text,
    put_progress,
    run_worker_task,
    user_error_from_payload,
)


def drain_messages(messages: queue.Queue[object]) -> list[GuiWorkerMessage]:
    items: list[GuiWorkerMessage] = []
    while not messages.empty():
        message = coerce_worker_message(messages.get_nowait())
        assert message is not None
        items.append(message)
    return items


def test_progress_message_is_string_safe() -> None:
    message = make_progress_message(123)

    assert message.kind == "progress"
    assert message.payload == "123"


def test_put_progress_uses_queue_compatible_sink() -> None:
    messages: queue.Queue[object] = queue.Queue()

    put_progress(messages, "working")

    assert messages.get_nowait() == GuiWorkerMessage("progress", "working")


def test_coerce_worker_message_accepts_legacy_tuple() -> None:
    assert coerce_worker_message(("progress", "old")) == GuiWorkerMessage("progress", "old")


def test_coerce_worker_message_rejects_unknown_payloads() -> None:
    assert coerce_worker_message(("nope", "old")) is None
    assert coerce_worker_message(object()) is None


def test_run_worker_task_emits_success_then_finished() -> None:
    messages: queue.Queue[object] = queue.Queue()

    run_worker_task(sink=messages, task=lambda: "done", success_kind="export_success")

    drained = drain_messages(messages)
    assert drained == [GuiWorkerMessage("export_success", "done"), GuiWorkerMessage("export_finished")]


def test_run_worker_task_emits_user_error_then_finished() -> None:
    messages: queue.Queue[object] = queue.Queue()

    def broken_task() -> str:
        raise RuntimeError("worker boom")

    run_worker_task(sink=messages, task=broken_task, success_kind="batch_success", logger=logging.getLogger("test"))

    drained = drain_messages(messages)
    assert drained[0].kind == "export_error"
    assert isinstance(drained[0].payload, UserFacingError)
    assert drained[0].payload.summary == "worker boom"
    assert drained[1] == GuiWorkerMessage("export_finished")


def test_user_error_from_payload_preserves_new_error_payload() -> None:
    payload = user_error_from_payload(RuntimeError("old string payload"))

    assert payload.summary == "old string payload"
    assert message_payload_text(payload).startswith("old string payload")
