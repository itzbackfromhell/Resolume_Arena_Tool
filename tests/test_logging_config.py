import logging

from resolume_alpha_tool.core import logging_config
from resolume_alpha_tool.core.gui_settings import CONFIG_ENV_VAR


def test_log_file_path_uses_config_env(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv(CONFIG_ENV_VAR, str(tmp_path))

    assert logging_config.log_file_path() == tmp_path / logging_config.LOG_FILE_NAME


def test_configure_logging_writes_project_log(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv(CONFIG_ENV_VAR, str(tmp_path))

    logger = logging_config.configure_logging(verbose=False, log_to_file=True)
    logger.info("hello log")
    for handler in logger.handlers:
        handler.flush()

    assert (tmp_path / logging_config.LOG_FILE_NAME).read_text(encoding="utf-8").strip().endswith(
        "INFO resolume_alpha_tool: hello log"
    )


def test_configure_logging_is_idempotent(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv(CONFIG_ENV_VAR, str(tmp_path))

    first = logging_config.configure_logging(verbose=False, log_to_file=True)
    first_count = len(first.handlers)
    second = logging_config.configure_logging(verbose=False, log_to_file=True)

    assert second is first
    assert len(second.handlers) == first_count


def test_configure_logging_can_disable_file_handler(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv(CONFIG_ENV_VAR, str(tmp_path))

    logger = logging_config.configure_logging(verbose=False, log_to_file=False)

    assert not (tmp_path / logging_config.LOG_FILE_NAME).exists()
    assert any(isinstance(handler, logging.NullHandler) for handler in logger.handlers)
