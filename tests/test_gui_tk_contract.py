import tkinter as tk

from resolume_alpha_tool.app import AlphaDropperApp


def test_gui_does_not_override_tk_options_internal() -> None:
    assert "_options" not in AlphaDropperApp.__dict__
    assert callable(tk.Tk._options)
