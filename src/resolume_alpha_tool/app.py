"""Focused Tkinter GUI for background-removed alpha image exports."""

from __future__ import annotations

import contextlib
import ctypes
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import cast

from PIL import Image, ImageTk

from .core.alpha_diagnostics import AlphaDiagnostics, analyze_alpha_image_object
from .core.batch_export import BatchExportRequest, BatchExportSummary, export_batch, normalize_batch_targets
from .core.gui_settings import load_json_object, save_json_object, settings_path
from .core.input_resolver import SUPPORTED_IMAGE_SUFFIXES, clean_path_text
from .core.models import ExportTarget, FitMode, ProcessingOptions, ProcessResult
from .core.resolume_export import (
    RESOLUME_CANVAS_SIZE,
    RESOLUME_OUTPUT_FORMAT,
    RESOLUME_OUTPUT_SUFFIX,
    SHIRT_PRINT_OUTPUT_SUFFIX,
    ExportJob,
    export_alpha_image,
    normalize_export_target,
    normalize_resolume_preset,
    processing_options_for_target,
    resolume_processing_options,
    shirt_print_processing_options,
)
from .core.validation import ensure_file

__all__ = [
    "AlphaDropperApp",
    "ExportJob",
    "RESOLUME_CANVAS_SIZE",
    "RESOLUME_OUTPUT_FORMAT",
    "RESOLUME_OUTPUT_SUFFIX",
    "SHIRT_PRINT_OUTPUT_SUFFIX",
    "processing_options_for_target",
    "resolume_processing_options",
]

IMAGE_FILETYPES = [("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("All", "*.*")]
PREVIEW_SIZE = (420, 300)
TARGET_LABELS: dict[ExportTarget, str] = {
    "resolume": "Resolume PNG",
    "shirt_print": "Shirt/Print PNG",
}
RESOLUME_PRESET_LABELS = {
    "1080p": "Resolume 1080p",
    "4k": "Resolume 4K",
    "square_1080": "Square 1080",
}
PREVIEW_MODE_LABELS = {
    "checker": "Checker",
    "black": "Black",
    "white": "White",
    "alpha": "Alpha matte",
}
EDGE_PROFILE_LABELS = {
    "normal": "Normal",
    "soft": "Soft feather",
    "tight": "Tight cut",
    "grow": "Grow edge",
}
DARK_THEME = {
    "background": "#000000",
    "panel": "#000000",
    "panel_alt": "#000000",
    "field": "#000000",
    "text": "#f4fff4",
    "muted": "#b7c7b7",
    "disabled": "#536153",
    "heading": "#39ff14",
    "accent": "#39ff14",
    "accent_hover": "#6dff4f",
    "accent_pressed": "#25b80f",
    "border": "#164d12",
    "error": "#ff4d4d",
}
DARK_CHECKER_BASE = (0, 0, 0, 255)
DARK_CHECKER_ALT = (5, 18, 5, 255)
WINDOWS_GA_ROOT = 2
WINDOWS_DWMWA_BORDER_COLOR = 34
WINDOWS_DWMWA_CAPTION_COLOR = 35
WINDOWS_DWMWA_TEXT_COLOR = 36
WINDOWS_DARK_MODE_ATTRIBUTES = (20, 19)


def _hex_to_windows_colorref(hex_color: str) -> int:
    """Convert #RRGGBB to Windows COLORREF 0x00bbggrr."""

    value = hex_color.removeprefix("#")
    if len(value) != 6:
        raise ValueError(f"Expected #RRGGBB color, got {hex_color!r}")
    red = int(value[0:2], 16)
    green = int(value[2:4], 16)
    blue = int(value[4:6], 16)
    return red | (green << 8) | (blue << 16)


def _settings_int(settings: dict[str, object], key: str, default: int) -> int:
    value = settings.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _settings_bool(settings: dict[str, object], key: str, default: bool = False) -> bool:
    value = settings.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "yes", "true", "on"}
    return bool(value)


class AlphaDropperApp(tk.Tk):
    """Desktop GUI for single-image and folder alpha PNG exports."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Alpha PNG Exporter")
        self.geometry("980x780")
        self.minsize(860, 680)
        self._apply_dark_theme()
        self.after(0, self._apply_windows_dark_titlebar)
        self.after(250, self._apply_windows_dark_titlebar)
        self.bind("<Map>", lambda _event: self.after(50, self._apply_windows_dark_titlebar), add="+")

        self.settings = load_json_object(settings_path())
        if isinstance(self.settings.get("window_geometry"), str):
            self.geometry(str(self.settings["window_geometry"]))

        self.worker: threading.Thread | None = None
        self.messages: queue.Queue[object] = queue.Queue()
        self.input_preview_ref: ImageTk.PhotoImage | None = None
        self.output_preview_ref: ImageTk.PhotoImage | None = None
        self.last_output_path: Path | None = None

        saved_target = str(self.settings.get("export_target", "resolume"))
        try:
            normalized_target = normalize_export_target(saved_target)
        except Exception:
            normalized_target = "resolume"

        self.input_var = tk.StringVar(value=str(self.settings.get("input_path", "")))
        self.batch_dir_var = tk.StringVar(value=str(self.settings.get("batch_dir", "")))
        self.output_var = tk.StringVar(value=str(self.settings.get("output_dir", Path.cwd() / "output")))
        self.export_target_var = tk.StringVar(value=normalized_target)
        self.resolume_preset_var = tk.StringVar(value=str(self.settings.get("resolume_preset", "1080p")))
        self.fit_mode_var = tk.StringVar(value=str(self.settings.get("fit_mode", "contain")))
        self.preview_mode_var = tk.StringVar(value=str(self.settings.get("preview_mode", "checker")))
        self.edge_profile_var = tk.StringVar(value=str(self.settings.get("edge_profile", "normal")))
        self.shirt_padding_var = tk.IntVar(value=_settings_int(self.settings, "shirt_padding", 96))
        self.batch_both_targets_var = tk.BooleanVar(
            value=_settings_bool(self.settings, "batch_both_targets")
        )
        self.batch_recursive_var = tk.BooleanVar(value=_settings_bool(self.settings, "batch_recursive"))
        self.open_after_export_var = tk.BooleanVar(
            value=_settings_bool(self.settings, "open_after_export")
        )
        self.status_var = tk.StringVar(value="Ready")
        self.input_status_var = tk.StringVar(value="No input selected.")
        self.output_status_var = tk.StringVar(value="No export yet.")
        self.result_var = tk.StringVar(value="Select one image or a batch folder, then choose export options.")
        self.mode_help_var = tk.StringVar(value="")
        self.progress_var = tk.DoubleVar(value=0)

        self._build_ui()
        self._bind_events()
        self._update_input_status()
        self._update_mode_help()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._drain_messages)

    def _windows_hwnd_candidates(self) -> list[int]:
        """Return likely Tk top-level HWNDs for native Windows DWM styling."""

        if not sys.platform.startswith("win"):
            return []

        handles: list[int] = []
        with contextlib.suppress(AttributeError, OSError, tk.TclError):
            raw_hwnd = int(self.winfo_id())
            handles.append(raw_hwnd)

            user32 = ctypes.windll.user32
            for candidate in (
                user32.GetParent(raw_hwnd),
                user32.GetAncestor(raw_hwnd, WINDOWS_GA_ROOT),
            ):
                candidate_int = int(candidate)
                if candidate_int:
                    handles.append(candidate_int)

        unique_handles: list[int] = []
        for hwnd in handles:
            if hwnd and hwnd not in unique_handles:
                unique_handles.append(hwnd)
        return unique_handles

    def _set_windows_dwm_attribute(self, hwnd: int, attribute: int, value: int) -> bool:
        """Set one integer DWM attribute on one HWND."""

        with contextlib.suppress(AttributeError, OSError):
            payload = ctypes.c_int(value)
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd),
                ctypes.c_int(attribute),
                ctypes.byref(payload),
                ctypes.c_int(ctypes.sizeof(payload)),
            )
            return result == 0
        return False

    def _apply_windows_dark_titlebar(self) -> None:
        """Ask Windows DWM to use a black native title bar when available."""

        if not sys.platform.startswith("win"):
            return

        with contextlib.suppress(tk.TclError):
            self.update_idletasks()

        caption_color = _hex_to_windows_colorref(DARK_THEME["background"])
        text_color = _hex_to_windows_colorref(DARK_THEME["heading"])
        border_color = _hex_to_windows_colorref(DARK_THEME["border"])

        for hwnd in self._windows_hwnd_candidates():
            for attribute in WINDOWS_DARK_MODE_ATTRIBUTES:
                self._set_windows_dwm_attribute(hwnd, attribute, 1)
            self._set_windows_dwm_attribute(hwnd, WINDOWS_DWMWA_CAPTION_COLOR, caption_color)
            self._set_windows_dwm_attribute(hwnd, WINDOWS_DWMWA_TEXT_COLOR, text_color)
            self._set_windows_dwm_attribute(hwnd, WINDOWS_DWMWA_BORDER_COLOR, border_color)

    def _apply_dark_theme(self) -> None:
        """Apply a black/neon ttk theme across the focused desktop UI."""

        self.configure(bg=DARK_THEME["background"])
        self.option_add("*Background", DARK_THEME["background"])
        self.option_add("*Foreground", DARK_THEME["text"])
        self.option_add("*selectBackground", DARK_THEME["accent"])
        self.option_add("*selectForeground", DARK_THEME["background"])
        self.option_add("*insertBackground", DARK_THEME["heading"])

        style = ttk.Style(self)
        with contextlib.suppress(tk.TclError):
            style.theme_use("clam")

        style.configure(
            ".",
            background=DARK_THEME["background"],
            foreground=DARK_THEME["text"],
            fieldbackground=DARK_THEME["field"],
            bordercolor=DARK_THEME["border"],
            lightcolor=DARK_THEME["border"],
            darkcolor=DARK_THEME["border"],
            troughcolor=DARK_THEME["field"],
            focuscolor=DARK_THEME["heading"],
            font=("Segoe UI", 10),
        )
        style.configure("TFrame", background=DARK_THEME["background"])
        style.configure(
            "TLabelframe",
            background=DARK_THEME["panel"],
            bordercolor=DARK_THEME["border"],
            relief="solid",
        )
        style.configure(
            "TLabelframe.Label",
            background=DARK_THEME["background"],
            foreground=DARK_THEME["heading"],
            font=("Segoe UI", 10, "bold"),
        )
        style.configure("TLabel", background=DARK_THEME["background"], foreground=DARK_THEME["text"])
        style.configure(
            "Title.TLabel",
            background=DARK_THEME["background"],
            foreground=DARK_THEME["heading"],
            font=("Segoe UI", 18, "bold"),
        )
        style.configure(
            "Muted.TLabel",
            background=DARK_THEME["background"],
            foreground=DARK_THEME["muted"],
        )
        style.configure(
            "Preview.TLabel",
            background=DARK_THEME["panel_alt"],
            foreground=DARK_THEME["muted"],
            bordercolor=DARK_THEME["border"],
            relief="solid",
            padding=12,
        )
        style.configure(
            "TButton",
            background=DARK_THEME["background"],
            foreground=DARK_THEME["heading"],
            bordercolor=DARK_THEME["heading"],
            focusthickness=1,
            focuscolor=DARK_THEME["accent_hover"],
            padding=(10, 7),
            relief="solid",
        )
        style.map(
            "TButton",
            background=[
                ("disabled", DARK_THEME["background"]),
                ("pressed", DARK_THEME["accent_pressed"]),
                ("active", DARK_THEME["accent"]),
            ],
            foreground=[
                ("disabled", DARK_THEME["disabled"]),
                ("pressed", DARK_THEME["background"]),
                ("active", DARK_THEME["background"]),
            ],
            bordercolor=[
                ("disabled", DARK_THEME["border"]),
                ("pressed", DARK_THEME["accent_pressed"]),
                ("active", DARK_THEME["accent_hover"]),
            ],
        )
        style.configure(
            "TEntry",
            fieldbackground=DARK_THEME["field"],
            foreground=DARK_THEME["text"],
            insertcolor=DARK_THEME["heading"],
            bordercolor=DARK_THEME["border"],
            lightcolor=DARK_THEME["border"],
            darkcolor=DARK_THEME["border"],
            padding=(6, 5),
        )
        style.map(
            "TEntry",
            fieldbackground=[("disabled", DARK_THEME["panel_alt"])],
            foreground=[("disabled", DARK_THEME["disabled"])],
            bordercolor=[("focus", DARK_THEME["heading"])],
        )
        style.configure(
            "TRadiobutton",
            background=DARK_THEME["panel"],
            foreground=DARK_THEME["text"],
            indicatorcolor=DARK_THEME["field"],
            focuscolor=DARK_THEME["heading"],
            padding=4,
        )
        style.map(
            "TRadiobutton",
            background=[
                ("active", DARK_THEME["background"]),
                ("selected", DARK_THEME["panel"]),
            ],
            foreground=[
                ("disabled", DARK_THEME["disabled"]),
                ("active", DARK_THEME["heading"]),
            ],
            indicatorcolor=[
                ("selected", DARK_THEME["heading"]),
                ("pressed", DARK_THEME["accent_pressed"]),
                ("active", DARK_THEME["accent_hover"]),
            ],
        )
        style.configure(
            "TCheckbutton",
            background=DARK_THEME["background"],
            foreground=DARK_THEME["text"],
            indicatorcolor=DARK_THEME["field"],
            focuscolor=DARK_THEME["heading"],
        )
        style.configure(
            "TCombobox",
            fieldbackground=DARK_THEME["field"],
            foreground=DARK_THEME["text"],
            arrowcolor=DARK_THEME["heading"],
        )
        style.configure(
            "TProgressbar",
            background=DARK_THEME["heading"],
            troughcolor=DARK_THEME["field"],
            bordercolor=DARK_THEME["border"],
        )

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=14)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(2, weight=1)

        ttk.Label(root, text="Alpha PNG Exporter", style="Title.TLabel").grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
        )
        ttk.Label(
            root,
            text="Single or batch alpha PNG export for Resolume, VJ assets, and shirt/print PNGs.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))
        ttk.Label(root, textvariable=self.status_var, style="Muted.TLabel").grid(
            row=0,
            column=1,
            sticky="e",
        )

        self._build_preview_panel(root)
        self._build_path_panel(root)
        self._build_mode_panel(root)
        self._build_action_panel(root)

    def _build_preview_panel(self, root: ttk.Frame) -> None:
        input_box = ttk.LabelFrame(root, text="Input", padding=10)
        input_box.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        input_box.rowconfigure(0, weight=1)
        input_box.columnconfigure(0, weight=1)

        output_box = ttk.LabelFrame(root, text="Exported", padding=10)
        output_box.grid(row=2, column=1, sticky="nsew", padx=(8, 0))
        output_box.rowconfigure(0, weight=1)
        output_box.columnconfigure(0, weight=1)

        self.input_preview_label = ttk.Label(
            input_box,
            text="Select an image.",
            anchor="center",
            style="Preview.TLabel",
        )
        self.input_preview_label.grid(row=0, column=0, sticky="nsew")
        ttk.Label(input_box, textvariable=self.input_status_var, style="Muted.TLabel", wraplength=410).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(8, 0),
        )

        self.output_preview_label = ttk.Label(
            output_box,
            text="Export result appears here.",
            anchor="center",
            style="Preview.TLabel",
        )
        self.output_preview_label.grid(row=0, column=0, sticky="nsew")
        ttk.Label(output_box, textvariable=self.output_status_var, style="Muted.TLabel", wraplength=410).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(8, 0),
        )

    def _build_path_panel(self, root: ttk.Frame) -> None:
        panel = ttk.LabelFrame(root, text="Paths", padding=10)
        panel.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 8))
        panel.columnconfigure(1, weight=1)

        ttk.Label(panel, text="Input image").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.input_entry = ttk.Entry(panel, textvariable=self.input_var)
        self.input_entry.grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Button(panel, text="Choose image", command=self._browse_input).grid(
            row=0,
            column=2,
            sticky="ew",
            padx=(8, 0),
        )

        ttk.Label(panel, text="Batch folder").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        self.batch_entry = ttk.Entry(panel, textvariable=self.batch_dir_var)
        self.batch_entry.grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Button(panel, text="Choose folder", command=self._browse_batch_dir).grid(
            row=1,
            column=2,
            sticky="ew",
            padx=(8, 0),
        )

        ttk.Label(panel, text="Output folder").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(panel, textvariable=self.output_var).grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Button(panel, text="Choose folder", command=self._browse_output).grid(
            row=2,
            column=2,
            sticky="ew",
            padx=(8, 0),
        )

    def _build_mode_panel(self, root: ttk.Frame) -> None:
        panel = ttk.LabelFrame(root, text="Export options", padding=10)
        panel.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        for column in range(6):
            panel.columnconfigure(column, weight=1)

        ttk.Radiobutton(
            panel,
            text="Resolume",
            value="resolume",
            variable=self.export_target_var,
            command=self._update_mode_help,
        ).grid(row=0, column=0, sticky="w", padx=(0, 18))
        ttk.Radiobutton(
            panel,
            text="Shirt/Print",
            value="shirt_print",
            variable=self.export_target_var,
            command=self._update_mode_help,
        ).grid(row=0, column=1, sticky="w", padx=(0, 18))
        ttk.Checkbutton(panel, text="Batch both", variable=self.batch_both_targets_var).grid(
            row=0,
            column=2,
            sticky="w",
            padx=(0, 18),
        )
        ttk.Checkbutton(panel, text="Recursive", variable=self.batch_recursive_var).grid(
            row=0,
            column=3,
            sticky="w",
            padx=(0, 18),
        )
        ttk.Checkbutton(panel, text="Open folder after export", variable=self.open_after_export_var).grid(
            row=0,
            column=4,
            columnspan=2,
            sticky="w",
        )

        ttk.Label(panel, text="Resolume preset", style="Muted.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Combobox(
            panel,
            textvariable=self.resolume_preset_var,
            values=tuple(RESOLUME_PRESET_LABELS),
            state="readonly",
            width=14,
        ).grid(row=2, column=0, sticky="ew", padx=(0, 8), pady=(2, 0))

        ttk.Label(panel, text="Fit", style="Muted.TLabel").grid(row=1, column=1, sticky="w")
        ttk.Combobox(
            panel,
            textvariable=self.fit_mode_var,
            values=("contain", "cover", "stretch"),
            state="readonly",
            width=12,
        ).grid(row=2, column=1, sticky="ew", padx=(0, 8), pady=(2, 0))

        ttk.Label(panel, text="Shirt padding", style="Muted.TLabel").grid(row=1, column=2, sticky="w")
        ttk.Spinbox(
            panel,
            textvariable=self.shirt_padding_var,
            from_=0,
            to=320,
            increment=16,
            width=10,
        ).grid(row=2, column=2, sticky="ew", padx=(0, 8), pady=(2, 0))

        ttk.Label(panel, text="Edge cleanup", style="Muted.TLabel").grid(row=1, column=3, sticky="w")
        ttk.Combobox(
            panel,
            textvariable=self.edge_profile_var,
            values=tuple(EDGE_PROFILE_LABELS),
            state="readonly",
            width=14,
        ).grid(row=2, column=3, sticky="ew", padx=(0, 8), pady=(2, 0))

        ttk.Label(panel, text="Preview", style="Muted.TLabel").grid(row=1, column=4, sticky="w")
        ttk.Combobox(
            panel,
            textvariable=self.preview_mode_var,
            values=tuple(PREVIEW_MODE_LABELS),
            state="readonly",
            width=14,
        ).grid(row=2, column=4, sticky="ew", padx=(0, 8), pady=(2, 0))

        ttk.Label(panel, textvariable=self.mode_help_var, style="Muted.TLabel", wraplength=280).grid(
            row=1,
            column=5,
            rowspan=2,
            sticky="w",
        )

    def _build_action_panel(self, root: ttk.Frame) -> None:
        panel = ttk.Frame(root)
        panel.grid(row=5, column=0, columnspan=2, sticky="ew")
        for column in range(3):
            panel.columnconfigure(column, weight=1)

        self.export_button = ttk.Button(
            panel,
            text="Convert image",
            command=self._start_export,
        )
        self.export_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.batch_button = ttk.Button(
            panel,
            text="Convert folder",
            command=self._start_batch_export,
        )
        self.batch_button.grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(panel, text="Open output folder", command=self._open_output_folder).grid(
            row=0,
            column=2,
            sticky="ew",
            padx=(6, 0),
        )
        self.progress_bar = ttk.Progressbar(
            panel,
            variable=self.progress_var,
            mode="indeterminate",
            maximum=100,
        )
        self.progress_bar.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        ttk.Label(panel, textvariable=self.result_var, style="Muted.TLabel", wraplength=920).grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(8, 0),
        )

    def _bind_events(self) -> None:
        self.input_var.trace_add("write", lambda *_: self._update_input_status())
        self.export_target_var.trace_add("write", lambda *_: self._update_mode_help())
        self.preview_mode_var.trace_add("write", lambda *_: self._refresh_previews())
        self.input_entry.bind("<Return>", lambda *_: self._update_input_status())
        self.input_entry.bind("<FocusOut>", lambda *_: self._update_input_status())

    def _browse_input(self) -> None:
        selected = filedialog.askopenfilename(title="Select one image", filetypes=IMAGE_FILETYPES)
        if selected:
            self.input_var.set(selected)

    def _browse_batch_dir(self) -> None:
        selected = filedialog.askdirectory(title="Select batch input folder")
        if selected:
            self.batch_dir_var.set(selected)

    def _browse_output(self) -> None:
        selected = filedialog.askdirectory(title="Select output folder")
        if selected:
            self.output_var.set(selected)

    def _input_path(self) -> Path | None:
        raw = clean_path_text(self.input_var.get())
        return Path(raw).expanduser() if raw else None

    def _batch_dir(self) -> Path | None:
        raw = clean_path_text(self.batch_dir_var.get())
        return Path(raw).expanduser() if raw else None

    def _output_dir(self) -> Path:
        raw = clean_path_text(self.output_var.get())
        return Path(raw).expanduser() if raw else Path.cwd() / "output"

    def _export_target(self) -> ExportTarget:
        try:
            return normalize_export_target(self.export_target_var.get())
        except Exception:
            self.export_target_var.set("resolume")
            return "resolume"

    def _fit_mode(self) -> FitMode:
        value = self.fit_mode_var.get().strip().lower()
        if value not in {"contain", "cover", "stretch"}:
            self.fit_mode_var.set("contain")
            return "contain"
        return cast(FitMode, value)

    def _shirt_padding(self) -> int:
        try:
            return max(0, int(self.shirt_padding_var.get()))
        except (TypeError, ValueError, tk.TclError):
            self.shirt_padding_var.set(96)
            return 96

    def _edge_profile(self) -> str:
        value = self.edge_profile_var.get().strip().lower().replace("-", "_")
        if value not in EDGE_PROFILE_LABELS:
            self.edge_profile_var.set("normal")
            return "normal"
        return value

    def _processing_options_for_target(self, target: ExportTarget) -> ProcessingOptions:
        edge_profile = self._edge_profile()
        if target == "shirt_print":
            return shirt_print_processing_options(
                padding=self._shirt_padding(),
                edge_profile=edge_profile,
            )
        try:
            canvas_size = normalize_resolume_preset(self.resolume_preset_var.get())
        except Exception:
            self.resolume_preset_var.set("1080p")
            canvas_size = RESOLUME_CANVAS_SIZE
        return resolume_processing_options(
            canvas_size=canvas_size,
            fit_mode=self._fit_mode(),
            edge_profile=edge_profile,
        )

    def _update_mode_help(self) -> None:
        target = self._export_target()
        if target == "shirt_print":
            self.mode_help_var.set("Trimmed transparent PNG with padding and tighter alpha cleanup.")
            button_text = "Convert for Shirt/Print"
        else:
            self.mode_help_var.set("Transparent PNG canvas for Resolume Arena/Avenue visuals.")
            button_text = "Convert for Resolume"

        if hasattr(self, "export_button"):
            self.export_button.configure(text=button_text)

    def _update_input_status(self) -> None:
        path = self._input_path()
        if path is None:
            self.input_status_var.set("No input selected.")
            self.input_preview_label.configure(text="Select an image.", image="")
            return
        if not path.exists():
            self.input_status_var.set(f"Input path does not exist: {path}")
            self.input_preview_label.configure(text="Input path does not exist.", image="")
            return
        if not path.is_file():
            self.input_status_var.set("Select exactly one image file, not a folder.")
            self.input_preview_label.configure(text="Select one image file.", image="")
            return
        if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            self.input_status_var.set(f"Unsupported image type: {path.suffix or 'no extension'}")
            self.input_preview_label.configure(text="Unsupported image type.", image="")
            return
        self._load_preview(path, target="input")

    def _start_export(self) -> None:
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Busy", "Export is already running.")
            return

        input_path = self._input_path()
        if input_path is None:
            messagebox.showerror("Missing input", "Select one input image first.")
            return
        try:
            source = ensure_file(input_path)
            target = self._export_target()
            options = self._processing_options_for_target(target)
        except Exception as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        job = ExportJob(input_path=source, output_dir=self._output_dir(), target=target, options=options)
        self._save_settings()
        self._set_busy(True)
        label = TARGET_LABELS[job.target]
        self.status_var.set("Exporting...")
        self.result_var.set(f"Removing background and writing {label}...")
        self.worker = threading.Thread(target=self._export_worker_fn, args=(job,), daemon=True)
        self.worker.start()

    def _start_batch_export(self) -> None:
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Busy", "Export is already running.")
            return

        batch_dir = self._batch_dir()
        if batch_dir is None:
            messagebox.showerror("Missing batch folder", "Select one batch folder first.")
            return

        try:
            target_values = ["resolume", "shirt-print"] if self.batch_both_targets_var.get() else [
                self.export_target_var.get()
            ]
            targets = normalize_batch_targets(target_values)
            options_by_target = {target: self._processing_options_for_target(target) for target in targets}
            request = BatchExportRequest(
                input_dir=batch_dir,
                output_dir=self._output_dir(),
                targets=targets,
                recursive=bool(self.batch_recursive_var.get()),
                options_by_target=options_by_target,
            )
        except Exception as exc:
            messagebox.showerror("Invalid batch", str(exc))
            return

        self._save_settings()
        self._set_busy(True)
        self.status_var.set("Batch exporting...")
        self.result_var.set("Removing backgrounds and writing batch PNGs...")
        self.worker = threading.Thread(target=self._batch_worker_fn, args=(request,), daemon=True)
        self.worker.start()

    def _set_busy(self, busy: bool) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        self.export_button.configure(state=state)
        self.batch_button.configure(state=state)
        if busy:
            self.progress_bar.start(12)
        else:
            self.progress_bar.stop()
            self.progress_var.set(0)

    def _export_worker_fn(self, job: ExportJob) -> None:
        try:
            result = export_alpha_image(
                job.input_path,
                job.output_dir,
                target=job.target,
                model=job.model,
                options=job.options,
                on_progress=lambda text: self.messages.put(("progress", text)),
            )
            self.messages.put(("export_success", result))
        except Exception as exc:
            self.messages.put(("export_error", str(exc)))
        finally:
            self.messages.put(("export_finished", None))

    def _batch_worker_fn(self, request: BatchExportRequest) -> None:
        try:
            summary = export_batch(
                request,
                on_progress=lambda text: self.messages.put(("progress", text)),
            )
            self.messages.put(("batch_success", summary))
        except Exception as exc:
            self.messages.put(("export_error", str(exc)))
        finally:
            self.messages.put(("export_finished", None))

    def _drain_messages(self) -> None:
        try:
            while True:
                message = self.messages.get_nowait()
                if not isinstance(message, tuple):
                    continue
                kind, payload = message
                if kind == "progress":
                    self.status_var.set("Working...")
                    self.result_var.set(str(payload))
                elif kind == "export_success" and isinstance(payload, ProcessResult):
                    self._handle_export_success(payload)
                elif kind == "batch_success" and isinstance(payload, BatchExportSummary):
                    self._handle_batch_success(payload)
                elif kind == "export_error":
                    self.status_var.set("Export failed")
                    self.result_var.set(f"Export failed: {payload}")
                elif kind == "export_finished":
                    self._set_busy(False)
                    self._update_mode_help()
                    if self.status_var.get() in {"Exporting...", "Batch exporting...", "Working..."}:
                        self.status_var.set("Ready")
        except queue.Empty:
            pass
        self.after(100, self._drain_messages)

    def _handle_export_success(self, result: ProcessResult) -> None:
        self.last_output_path = result.output_path
        self.status_var.set("Export complete")
        self.result_var.set(
            f"Saved {result.output_path.name} ({result.width}x{result.height}) -> "
            f"{result.output_path.parent}"
        )
        self._load_preview(result.output_path, target="output")
        self._save_settings()
        if self.open_after_export_var.get():
            self._open_folder_path(result.output_path.parent)

    def _handle_batch_success(self, summary: BatchExportSummary) -> None:
        self.status_var.set("Batch complete")
        self.result_var.set(
            f"Batch complete: {summary.exported_count} exported, "
            f"{summary.failed_count} failed -> {summary.output_dir}"
        )
        last_result = next((item.result for item in reversed(summary.items) if item.result), None)
        if last_result:
            self.last_output_path = last_result.output_path
            self._load_preview(last_result.output_path, target="output")
        self._save_settings()
        if self.open_after_export_var.get():
            self._open_folder_path(summary.output_dir)

    def _load_preview(self, path: Path, *, target: str) -> None:
        try:
            with Image.open(path) as image:
                rgba = image.convert("RGBA")
                diagnostics = analyze_alpha_image_object(image)
                photo = self._preview_photo(rgba)
        except OSError as exc:
            label = self.input_preview_label if target == "input" else self.output_preview_label
            label.configure(text=f"Preview failed: {exc}", image="")
            return

        status = self._diagnostics_text(path, diagnostics)
        if target == "input":
            self.input_preview_ref = photo
            self.input_preview_label.configure(image=self.input_preview_ref, text="")
            self.input_status_var.set(status)
        else:
            self.output_preview_ref = photo
            self.output_preview_label.configure(image=self.output_preview_ref, text="")
            self.output_status_var.set(status)

    def _diagnostics_text(self, path: Path, diagnostics: AlphaDiagnostics) -> str:
        text = f"{path.name}: {diagnostics.size_label}, {diagnostics.alpha_label}"
        if diagnostics.warnings:
            text = f"{text} | Warning: {diagnostics.warnings[0]}"
        return text

    def _refresh_previews(self) -> None:
        input_path = self._input_path()
        if input_path and input_path.exists() and input_path.is_file():
            self._load_preview(input_path, target="input")
        if self.last_output_path and self.last_output_path.exists():
            self._load_preview(self.last_output_path, target="output")

    def _preview_photo(self, image: Image.Image) -> ImageTk.PhotoImage:
        preview = image.copy()
        preview.thumbnail(PREVIEW_SIZE, Image.Resampling.LANCZOS)
        mode = self.preview_mode_var.get().strip().lower()
        if mode == "alpha":
            alpha = preview.getchannel("A")
            matte = Image.merge("RGBA", (alpha, alpha, alpha, Image.new("L", alpha.size, 255)))
            return ImageTk.PhotoImage(matte)
        if mode == "black":
            board = Image.new("RGBA", preview.size, (0, 0, 0, 255))
        elif mode == "white":
            board = Image.new("RGBA", preview.size, (255, 255, 255, 255))
        else:
            board = self._checkerboard(preview.size)
        board.alpha_composite(preview.convert("RGBA"))
        return ImageTk.PhotoImage(board)

    def _checkerboard(self, size: tuple[int, int]) -> Image.Image:
        canvas = Image.new("RGBA", size, DARK_CHECKER_BASE)
        tile = 12
        for y in range(0, size[1], tile):
            for x in range(0, size[0], tile):
                if ((x // tile) + (y // tile)) % 2:
                    canvas.paste(
                        DARK_CHECKER_ALT,
                        (x, y, min(x + tile, size[0]), min(y + tile, size[1])),
                    )
        return canvas

    def _open_output_folder(self) -> None:
        path = self._output_dir()
        self._open_folder_path(path)

    def _open_folder_path(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def _settings_payload(self) -> dict[str, str | int | bool]:
        return {
            "input_path": clean_path_text(self.input_var.get()),
            "batch_dir": clean_path_text(self.batch_dir_var.get()),
            "output_dir": clean_path_text(self.output_var.get()),
            "export_target": self.export_target_var.get(),
            "resolume_preset": self.resolume_preset_var.get(),
            "fit_mode": self.fit_mode_var.get(),
            "preview_mode": self.preview_mode_var.get(),
            "edge_profile": self.edge_profile_var.get(),
            "shirt_padding": self._shirt_padding(),
            "batch_both_targets": bool(self.batch_both_targets_var.get()),
            "batch_recursive": bool(self.batch_recursive_var.get()),
            "open_after_export": bool(self.open_after_export_var.get()),
            "window_geometry": self.geometry(),
        }

    def _save_settings(self) -> None:
        try:
            save_json_object(settings_path(), self._settings_payload())
        except Exception:
            return

    def _on_close(self) -> None:
        self._save_settings()
        self.destroy()


def main() -> None:
    app = AlphaDropperApp()
    app.mainloop()


if __name__ == "__main__":  # pragma: no cover
    main()
