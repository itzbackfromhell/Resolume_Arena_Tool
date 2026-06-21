from resolume_alpha_tool.core.error_ux import build_user_error
from resolume_alpha_tool.core.exceptions import DependencyMissingError, ProcessingError, ValidationError


def test_cli_error_text_keeps_legacy_error_prefix() -> None:
    user_error = build_user_error(ProcessingError("boom"))

    text = user_error.as_cli_text()

    assert text.startswith("ERROR: boom")
    assert "HINT:" in text
    assert "DETAIL:" not in text


def test_verbose_cli_error_includes_debug_detail() -> None:
    user_error = build_user_error(ProcessingError("alpha failed"))

    text = user_error.as_cli_text(verbose=True)

    assert "ERROR: alpha failed" in text
    assert "DETAIL: ProcessingError: alpha failed" in text


def test_dependency_error_points_to_rembg_check() -> None:
    user_error = build_user_error(DependencyMissingError("rembg missing"))

    assert user_error.title == "Missing dependency"
    assert "rembg-check" in user_error.recovery_hint


def test_validation_error_has_gui_recovery_hint() -> None:
    user_error = build_user_error(ValidationError("bad target"))

    text = user_error.as_gui_text()

    assert text.startswith("bad target")
    assert "What to try:" in text
    assert "target mode" in text
