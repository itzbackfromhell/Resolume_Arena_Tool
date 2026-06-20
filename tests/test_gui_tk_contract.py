import tkinter as tk

from resolume_alpha_tool.app import AlphaDropperApp, ExportJob


def test_gui_does_not_override_tk_options_internal() -> None:
    assert "_options" not in AlphaDropperApp.__dict__
    assert callable(tk.Tk._options)


def test_gui_export_flow_has_no_old_processing_aliases() -> None:
    assert "_start_processing" not in AlphaDropperApp.__dict__
    assert "_process_worker" not in AlphaDropperApp.__dict__
    assert "_start_export" in AlphaDropperApp.__dict__
    assert "_export_worker_fn" in AlphaDropperApp.__dict__


def test_gui_has_expected_usability_panels() -> None:
    assert "_build_effect_panel" in AlphaDropperApp.__dict__
    assert "_build_preset_panel" in AlphaDropperApp.__dict__
    assert "_save_settings" in AlphaDropperApp.__dict__
    assert "_cancel_export" in AlphaDropperApp.__dict__


def test_export_job_names_export_intent() -> None:
    assert ExportJob.__name__ == "ExportJob"
