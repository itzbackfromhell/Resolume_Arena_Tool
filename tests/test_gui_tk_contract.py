import tkinter as tk

from resolume_alpha_tool.app import (
    RESOLUME_CANVAS_SIZE,
    RESOLUME_OUTPUT_FORMAT,
    RESOLUME_OUTPUT_SUFFIX,
    SHIRT_PRINT_OUTPUT_SUFFIX,
    AlphaDropperApp,
    ExportJob,
    processing_options_for_target,
    resolume_processing_options,
)


def test_gui_does_not_override_tk_options_internal() -> None:
    assert "_options" not in AlphaDropperApp.__dict__
    assert callable(tk.Tk._options)


def test_gui_is_single_image_only_contract() -> None:
    assert "_start_export" in AlphaDropperApp.__dict__
    assert "_export_worker_fn" in AlphaDropperApp.__dict__
    assert "_browse_input" in AlphaDropperApp.__dict__
    assert "_browse_output" in AlphaDropperApp.__dict__
    assert "_refresh_queue" not in AlphaDropperApp.__dict__
    assert "_retry_failed_export" not in AlphaDropperApp.__dict__
    assert "_build_queue_panel" not in AlphaDropperApp.__dict__
    assert "_save_current_preset" not in AlphaDropperApp.__dict__


def test_resolume_processing_options_are_fixed_for_gui() -> None:
    options = resolume_processing_options()

    assert options.remove_background is True
    assert options.output_format == RESOLUME_OUTPUT_FORMAT == "png"
    assert options.suffix == RESOLUME_OUTPUT_SUFFIX == "_resolume"
    assert options.fit_mode == "contain"
    assert (options.canvas_width, options.canvas_height) == RESOLUME_CANVAS_SIZE == (1920, 1080)
    assert options.overwrite is False


def test_shirt_print_processing_options_are_available_for_gui() -> None:
    options = processing_options_for_target("shirt-print")

    assert options.remove_background is True
    assert options.output_format == RESOLUME_OUTPUT_FORMAT == "png"
    assert options.suffix == SHIRT_PRINT_OUTPUT_SUFFIX == "_shirt_print"
    assert options.fit_mode == "none"
    assert options.trim_to_alpha is True


def test_export_job_names_export_intent() -> None:
    assert ExportJob.__name__ == "ExportJob"
