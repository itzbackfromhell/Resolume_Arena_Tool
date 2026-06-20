"""Tkinter desktop GUI for Resolume Alpha Dropper."""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any

from PIL import Image, ImageTk

from .core.alpha_processor import process_image_object
from .core.batch import process_directory, process_single
from .core.gui_settings import (
    load_json_object,
    save_json_object,
    settings_path,
    user_presets_path,
)
from .core.input_resolver import SUPPORTED_IMAGE_SUFFIXES, clean_path_text, resolve_preview_source
from .core.models import ProcessingOptions
from .core.naming import build_output_path
from .core.preset_store import (
    CUSTOM_PRESET_NAME,
    clean_preset_name,
    merge_presets,
    normalize_presets,
    preset_from_options,
)
from .core.presets import load_presets
from .core.validation import SUPPORTED_IMAGE_EXTENSIONS, iter_images

IMAGE_FILETYPES = [("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("All", "*.*")]
PRESET_PATH = Path(__file__).resolve().parents[2] / "presets" / "defaults.json"
PREVIEW_SIZE = (340, 240)
REMOVEBG_MODELS = ["u2net", "u2netp", "isnet-general-use", "silueta", "birefnet-general"]


@dataclass(frozen=True)
class ExportJob:
    mode: str
    input_path: Path
    output_dir: Path
    options: ProcessingOptions
    open_output_after_export: bool = True
    recursive: bool = False


class AlphaDropperApp(tk.Tk):
    """Desktop GUI with persisted state, previews, progress, and preset management."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Resolume Alpha Dropper")
        self.geometry("1160x800")
        self.minsize(1040, 720)

        self.settings = load_json_object(settings_path())
        if isinstance(self.settings.get("window_geometry"), str):
            self.geometry(str(self.settings["window_geometry"]))

        self.default_presets = self._load_default_presets()
        self.user_presets = self._load_user_presets()
        self.presets = merge_presets(self.default_presets, self.user_presets)

        self.log_queue: queue.Queue[object] = queue.Queue()
        self.export_worker: threading.Thread | None = None
        self.preview_worker: threading.Thread | None = None
        self.cancel_export_event = threading.Event()
        self.preview_token = 0
        self.input_preview_ref: ImageTk.PhotoImage | None = None
        self.output_preview_ref: ImageTk.PhotoImage | None = None
        self.last_output_path: Path | None = None
        self.export_total = 0
        self.export_done = 0
        self._loading_preset = False

        self.input_var = tk.StringVar(value=str(self.settings.get("input_path", "")))
        self.output_var = tk.StringVar(value=str(self.settings.get("output_dir", Path.cwd() / "output")))
        self.mode_var = tk.StringVar(value=str(self.settings.get("mode", "single")))
        self.preset_var = tk.StringVar(value=str(self.settings.get("selected_preset", "resolume_1080p")))
        self.remove_bg_var = tk.BooleanVar(value=bool(self.settings.get("remove_background", False)))
        self.model_var = tk.StringVar(value=str(self.settings.get("rembg_model", "u2net")))
        self.threshold_var = tk.IntVar(value=int(self.settings.get("alpha_threshold", 8)))
        self.feather_var = tk.DoubleVar(value=float(self.settings.get("feather_radius", 0.8)))
        self.gamma_var = tk.DoubleVar(value=float(self.settings.get("alpha_gamma", 1.0)))
        self.despill_var = tk.DoubleVar(value=float(self.settings.get("despill_strength", 0.35)))
        self.fit_var = tk.StringVar(value=str(self.settings.get("fit_mode", "contain")))
        self.width_var = tk.IntVar(value=int(self.settings.get("canvas_width", 1920)))
        self.height_var = tk.IntVar(value=int(self.settings.get("canvas_height", 1080)))
        self.format_var = tk.StringVar(value=str(self.settings.get("output_format", "png")))
        self.suffix_var = tk.StringVar(value=str(self.settings.get("suffix", "_alpha")))
        self.overwrite_var = tk.BooleanVar(value=bool(self.settings.get("overwrite", False)))
        self.recursive_var = tk.BooleanVar(value=bool(self.settings.get("recursive", False)))
        self.open_after_export_var = tk.BooleanVar(
            value=bool(self.settings.get("open_output_after_export", True))
        )
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_text_var = tk.StringVar(value="Idle.")
        self.status_var = tk.StringVar(value="Ready")
        self.input_status_var = tk.StringVar(value="No input selected.")
        self.export_summary_var = tk.StringVar(value="No export yet.")

        self._build_ui()
        self._refresh_preset_choices()
        self._bind_preview_traces()
        self._update_input_status()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._drain_log_queue)

    def _load_default_presets(self) -> dict[str, dict[str, Any]]:
        try:
            return load_presets(PRESET_PATH)
        except Exception:
            return {}

    def _load_user_presets(self) -> dict[str, dict[str, Any]]:
        try:
            return normalize_presets(load_json_object(user_presets_path()))
        except ValueError:
            return {}

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(0, weight=0)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Resolume Alpha Dropper", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(header, text="Local transparent asset prep for Resolume Arena/Avenue.").grid(
            row=1, column=0, sticky="w"
        )
        ttk.Label(header, textvariable=self.status_var).grid(row=0, column=1, rowspan=2, sticky="e")

        left = ttk.Frame(root)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        left.columnconfigure(0, weight=1)

        right = ttk.Frame(root)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.columnconfigure(1, weight=1)
        right.rowconfigure(1, weight=1)
        right.rowconfigure(2, weight=1)

        self._build_mode_panel(left)
        self._build_path_panel(left)
        self._build_preset_panel(left)
        self._build_processing_panel(left)
        self._build_export_panel(left)
        self._build_action_panel(left)
        self._build_preview_panel(right)
        self._build_log_panel(right)

    def _build_mode_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Mode", padding=10)
        panel.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Radiobutton(
            panel,
            text="Single image",
            variable=self.mode_var,
            value="single",
            command=self._on_input_changed,
        ).pack(side=tk.LEFT)
        ttk.Radiobutton(
            panel,
            text="Batch folder",
            variable=self.mode_var,
            value="batch",
            command=self._on_input_changed,
        ).pack(side=tk.LEFT, padx=(12, 0))

    def _build_path_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Paths", padding=10)
        panel.grid(row=1, column=0, sticky="ew", pady=8)
        panel.columnconfigure(1, weight=1)

        ttk.Label(panel, text="Input").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.input_entry = ttk.Entry(panel, textvariable=self.input_var, width=46)
        self.input_entry.grid(row=0, column=1, sticky="ew", pady=4)
        self.input_entry.bind("<Return>", self._on_input_changed)
        self.input_entry.bind("<FocusOut>", self._on_input_changed)
        ttk.Button(panel, text="File", command=self._browse_input_file).grid(row=0, column=2, padx=(8, 0))
        ttk.Button(panel, text="Folder", command=self._browse_input_folder).grid(row=0, column=3, padx=(6, 0))

        ttk.Label(panel, text="Output folder").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(panel, textvariable=self.output_var, width=46).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Button(panel, text="Browse", command=self._browse_output).grid(row=1, column=2, columnspan=2, sticky="ew", padx=(8, 0))
        ttk.Label(panel, textvariable=self.input_status_var, foreground="#555555", wraplength=500).grid(
            row=2, column=0, columnspan=4, sticky="w", pady=(4, 0)
        )

    def _build_preset_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Presets", padding=10)
        panel.grid(row=2, column=0, sticky="ew", pady=8)
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)
        panel.columnconfigure(2, weight=1)

        self.preset_combo = ttk.Combobox(panel, textvariable=self.preset_var, state="readonly", width=28)
        self.preset_combo.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(0, 6), pady=3)
        self.preset_combo.bind("<<ComboboxSelected>>", lambda *_: self._apply_selected_preset())
        ttk.Button(panel, text="Apply", command=self._apply_selected_preset).grid(row=0, column=2, sticky="ew", pady=3)
        ttk.Button(panel, text="Save Current", command=self._save_current_preset).grid(row=1, column=0, sticky="ew", padx=(0, 3), pady=3)
        ttk.Button(panel, text="Delete", command=self._delete_selected_preset).grid(row=1, column=1, sticky="ew", padx=3, pady=3)
        ttk.Button(panel, text="Import", command=self._import_presets).grid(row=1, column=2, sticky="ew", padx=(3, 0), pady=3)
        ttk.Button(panel, text="Export Selected", command=self._export_selected_preset).grid(row=2, column=0, columnspan=3, sticky="ew", pady=3)

    def _build_processing_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Alpha cleanup", padding=10)
        panel.grid(row=3, column=0, sticky="ew", pady=8)
        for col in range(4):
            panel.columnconfigure(col, weight=1)

        ttk.Checkbutton(
            panel,
            text="Remove background",
            variable=self.remove_bg_var,
            command=self._refresh_preview,
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        ttk.Label(panel, text="Model").grid(row=1, column=0, sticky="w")
        ttk.Combobox(panel, textvariable=self.model_var, values=REMOVEBG_MODELS, width=18).grid(
            row=1, column=1, columnspan=3, sticky="ew"
        )

        self._spin(panel, "Threshold", self.threshold_var, 0, 255, 1, 2, 0)
        self._spin(panel, "Feather", self.feather_var, 0, 10, 0.1, 2, 2)
        self._spin(panel, "Gamma", self.gamma_var, 0.1, 4, 0.1, 3, 0)
        self._spin(panel, "Despill", self.despill_var, 0, 1, 0.05, 3, 2)

    def _spin(
        self,
        parent: ttk.Frame,
        label: str,
        var: tk.Variable,
        start: float,
        stop: float,
        step: float,
        row: int,
        col: int,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", pady=4)
        ttk.Spinbox(
            parent,
            from_=start,
            to=stop,
            increment=step,
            textvariable=var,
            width=8,
            command=self._refresh_preview,
        ).grid(row=row, column=col + 1, sticky="w", pady=4)

    def _build_export_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Export", padding=10)
        panel.grid(row=4, column=0, sticky="ew", pady=8)
        for col in range(4):
            panel.columnconfigure(col, weight=1)

        ttk.Label(panel, text="Fit").grid(row=0, column=0, sticky="w")
        ttk.Combobox(panel, textvariable=self.fit_var, values=["none", "contain", "cover", "stretch"], width=10).grid(row=0, column=1, sticky="w")
        ttk.Label(panel, text="Format").grid(row=0, column=2, sticky="w")
        ttk.Combobox(panel, textvariable=self.format_var, values=["png", "webp"], width=8).grid(row=0, column=3, sticky="w")
        ttk.Label(panel, text="Width").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Spinbox(panel, from_=1, to=16384, textvariable=self.width_var, width=8).grid(row=1, column=1, sticky="w", pady=4)
        ttk.Label(panel, text="Height").grid(row=1, column=2, sticky="w", pady=4)
        ttk.Spinbox(panel, from_=1, to=16384, textvariable=self.height_var, width=8).grid(row=1, column=3, sticky="w", pady=4)
        ttk.Label(panel, text="Suffix").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(panel, textvariable=self.suffix_var, width=12).grid(row=2, column=1, sticky="w", pady=4)
        ttk.Checkbutton(panel, text="Recursive batch", variable=self.recursive_var).grid(row=2, column=2, columnspan=2, sticky="w", pady=4)
        ttk.Checkbutton(panel, text="Overwrite", variable=self.overwrite_var).grid(row=3, column=0, sticky="w", pady=(4, 0))
        ttk.Checkbutton(panel, text="Open folder after export", variable=self.open_after_export_var).grid(row=3, column=1, columnspan=3, sticky="w", pady=(4, 0))

    def _build_action_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Actions", padding=10)
        panel.grid(row=5, column=0, sticky="ew", pady=8)
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)
        panel.columnconfigure(2, weight=1)

        self.preview_button = ttk.Button(panel, text="Preview", command=self._refresh_preview)
        self.preview_button.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=3)
        self.export_button = ttk.Button(panel, text="Export", command=self._start_export)
        self.export_button.grid(row=0, column=1, sticky="ew", padx=4, pady=3)
        self.cancel_button = ttk.Button(panel, text="Cancel", command=self._cancel_export, state=tk.DISABLED)
        self.cancel_button.grid(row=0, column=2, sticky="ew", padx=(4, 0), pady=3)
        ttk.Button(panel, text="Open output", command=self._open_output_folder).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=3)
        ttk.Button(panel, text="Clear log", command=self._clear_log).grid(row=1, column=1, columnspan=2, sticky="ew", padx=(4, 0), pady=3)
        self.progress_bar = ttk.Progressbar(panel, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 2))
        ttk.Label(panel, textvariable=self.progress_text_var, foreground="#555555", wraplength=480).grid(row=3, column=0, columnspan=3, sticky="w")
        ttk.Label(panel, textvariable=self.export_summary_var, foreground="#555555", wraplength=480).grid(row=4, column=0, columnspan=3, sticky="w", pady=(2, 0))

    def _build_preview_panel(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Preview", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        input_box = ttk.LabelFrame(parent, text="Input", padding=8)
        input_box.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        output_box = ttk.LabelFrame(parent, text="Processed", padding=8)
        output_box.grid(row=1, column=1, sticky="nsew", padx=(6, 0))

        self.input_preview_label = ttk.Label(input_box, text="Select an image.", anchor="center")
        self.input_preview_label.pack(fill=tk.BOTH, expand=True)
        self.output_preview_label = ttk.Label(output_box, text="Preview will appear here.", anchor="center")
        self.output_preview_label.pack(fill=tk.BOTH, expand=True)

    def _build_log_panel(self, parent: ttk.Frame) -> None:
        logs = ttk.LabelFrame(parent, text="Log", padding=8)
        logs.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        logs.rowconfigure(0, weight=1)
        logs.columnconfigure(0, weight=1)

        self.log_text = tk.Text(logs, height=10, wrap="word")
        scrollbar = ttk.Scrollbar(logs, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _bind_preview_traces(self) -> None:
        self.input_var.trace_add("write", lambda *_: self._on_input_changed())
        for var in (
            self.remove_bg_var,
            self.model_var,
            self.threshold_var,
            self.feather_var,
            self.gamma_var,
            self.despill_var,
            self.fit_var,
            self.width_var,
            self.height_var,
            self.format_var,
        ):
            var.trace_add("write", lambda *_: self._on_option_changed())

    def _refresh_preset_choices(self) -> None:
        default_names = sorted(self.default_presets)
        user_only_names = sorted(name for name in self.user_presets if name not in self.default_presets)
        shadow_names = sorted(name for name in self.user_presets if name in self.default_presets)
        names = [CUSTOM_PRESET_NAME, *default_names, *shadow_names, *user_only_names]
        seen: set[str] = set()
        unique_names = [name for name in names if not (name in seen or seen.add(name))]
        self.preset_combo.configure(values=unique_names)
        if self.preset_var.get() not in unique_names:
            self.preset_var.set(CUSTOM_PRESET_NAME)

    def _browse_input_file(self, *_args: object) -> None:
        selected = filedialog.askopenfilename(title="Select image", filetypes=IMAGE_FILETYPES)
        if selected:
            self.mode_var.set("single")
            self.input_var.set(selected)

    def _browse_input_folder(self, *_args: object) -> None:
        selected = filedialog.askdirectory(title="Select input folder")
        if selected:
            self.mode_var.set("batch")
            self.input_var.set(selected)

    def _browse_output(self, *_args: object) -> None:
        selected = filedialog.askdirectory(title="Select output folder")
        if selected:
            self.output_var.set(selected)

    def _on_input_changed(self, *_args: object) -> None:
        self._update_input_status()
        self._refresh_preview()

    def _on_option_changed(self, *_args: object) -> None:
        if not self._loading_preset:
            self.preset_var.set(CUSTOM_PRESET_NAME)
        self._refresh_preview()

    def _update_input_status(self, *_args: object) -> None:
        raw = clean_path_text(self.input_var.get())
        if not raw:
            self.input_status_var.set("No input selected.")
            return
        path = Path(raw).expanduser()
        if path.is_file():
            suffix = path.suffix.lower()
            if suffix in SUPPORTED_IMAGE_SUFFIXES:
                self.input_status_var.set(f"Input file ready: {path.name}")
            else:
                self.input_status_var.set(f"Unsupported file type: {suffix or 'no extension'}")
            return
        if path.is_dir():
            preview = resolve_preview_source(path)
            if preview:
                self.input_status_var.set(f"Input folder ready. Previewing: {preview.name}")
            else:
                self.input_status_var.set("Folder selected, but no supported images were found.")
            return
        self.input_status_var.set(f"Input path does not exist: {raw}")

    def _apply_selected_preset(self, *_args: object) -> None:
        self._apply_preset(self.preset_var.get())

    def _apply_preset(self, name: str, *_args: object) -> None:
        if name == CUSTOM_PRESET_NAME:
            self.status_var.set("Custom settings active")
            return
        preset = self.presets.get(name)
        if not preset:
            self._log(f"WARN preset not found: {name}")
            return

        self._loading_preset = True
        try:
            self.remove_bg_var.set(bool(preset.get("remove_background", self.remove_bg_var.get())))
            self.model_var.set(str(preset.get("rembg_model", self.model_var.get())))
            self.threshold_var.set(int(preset.get("alpha_threshold", self.threshold_var.get())))
            self.feather_var.set(float(preset.get("feather_radius", self.feather_var.get())))
            self.gamma_var.set(float(preset.get("alpha_gamma", self.gamma_var.get())))
            self.despill_var.set(float(preset.get("despill_strength", self.despill_var.get())))
            self.fit_var.set(str(preset.get("fit_mode", self.fit_var.get())))
            if preset.get("canvas_width"):
                self.width_var.set(int(preset["canvas_width"]))
            if preset.get("canvas_height"):
                self.height_var.set(int(preset["canvas_height"]))
            self.format_var.set(str(preset.get("output_format", self.format_var.get())))
            self.suffix_var.set(str(preset.get("suffix", self.suffix_var.get())))
            self.overwrite_var.set(bool(preset.get("overwrite", self.overwrite_var.get())))
        finally:
            self._loading_preset = False
        self.preset_var.set(name)
        self.status_var.set(f"Preset loaded: {name}")
        self._refresh_preview()

    def _save_current_preset(self, *_args: object) -> None:
        requested = simpledialog.askstring("Save preset", "Preset name:", parent=self)
        if requested is None:
            return
        try:
            name = clean_preset_name(requested)
        except ValueError as exc:
            messagebox.showerror("Invalid preset name", str(exc))
            return
        if name in self.presets and not messagebox.askyesno(
            "Overwrite preset", f"Preset '{name}' already exists. Overwrite it?"
        ):
            return
        self.user_presets[name] = preset_from_options(self._processing_options())
        save_json_object(user_presets_path(), self.user_presets)
        self.presets = merge_presets(self.default_presets, self.user_presets)
        self._refresh_preset_choices()
        self.preset_var.set(name)
        self.status_var.set(f"Preset saved: {name}")
        self._log(f"PRESET SAVED {name}")

    def _delete_selected_preset(self, *_args: object) -> None:
        name = self.preset_var.get()
        if name == CUSTOM_PRESET_NAME:
            return
        if name not in self.user_presets:
            messagebox.showinfo("Default preset", "Bundled presets cannot be deleted. Save an override first if needed.")
            return
        if not messagebox.askyesno("Delete preset", f"Delete user preset '{name}'?"):
            return
        del self.user_presets[name]
        save_json_object(user_presets_path(), self.user_presets)
        self.presets = merge_presets(self.default_presets, self.user_presets)
        self.preset_var.set(CUSTOM_PRESET_NAME)
        self._refresh_preset_choices()
        self.status_var.set(f"Preset deleted: {name}")
        self._log(f"PRESET DELETED {name}")

    def _import_presets(self, *_args: object) -> None:
        selected = filedialog.askopenfilename(title="Import presets", filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if not selected:
            return
        try:
            with Path(selected).open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                raise ValueError("Preset file must contain a JSON object.")
            imported = normalize_presets(data)
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc))
            return
        self.user_presets.update(imported)
        save_json_object(user_presets_path(), self.user_presets)
        self.presets = merge_presets(self.default_presets, self.user_presets)
        self._refresh_preset_choices()
        self.status_var.set(f"Imported {len(imported)} preset(s)")
        self._log(f"PRESETS IMPORTED {len(imported)} from {selected}")

    def _export_selected_preset(self, *_args: object) -> None:
        name = self.preset_var.get()
        if name == CUSTOM_PRESET_NAME:
            preset = preset_from_options(self._processing_options())
            name = "custom_current"
        else:
            preset = self.presets.get(name)
            if not preset:
                messagebox.showerror("Export failed", f"Preset not found: {name}")
                return
        selected = filedialog.asksaveasfilename(
            title="Export preset",
            defaultextension=".json",
            initialfile=f"{name.replace(' ', '_')}.json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not selected:
            return
        try:
            with Path(selected).open("w", encoding="utf-8") as handle:
                json.dump({name: preset}, handle, indent=2, sort_keys=True)
                handle.write("\n")
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        self.status_var.set(f"Preset exported: {Path(selected).name}")
        self._log(f"PRESET EXPORTED {selected}")

    def _processing_options(self, *_args: object) -> ProcessingOptions:
        fit_mode = self.fit_var.get()
        width = int(self.width_var.get()) if fit_mode != "none" else None
        height = int(self.height_var.get()) if fit_mode != "none" else None
        return ProcessingOptions(
            remove_background=bool(self.remove_bg_var.get()),
            rembg_model=self.model_var.get(),
            alpha_threshold=int(self.threshold_var.get()),
            feather_radius=float(self.feather_var.get()),
            alpha_gamma=float(self.gamma_var.get()),
            despill_strength=float(self.despill_var.get()),
            fit_mode=fit_mode,  # type: ignore[arg-type]
            canvas_width=width,
            canvas_height=height,
            output_format=self.format_var.get(),  # type: ignore[arg-type]
            overwrite=bool(self.overwrite_var.get()),
            suffix=self.suffix_var.get().strip() or "_alpha",
        )

    def _current_job(self, *_args: object) -> ExportJob | None:
        input_raw = clean_path_text(self.input_var.get())
        output_raw = clean_path_text(self.output_var.get())
        if not input_raw:
            return None
        input_path = Path(input_raw).expanduser()
        if not input_path.exists():
            return None
        output_dir = Path(output_raw).expanduser() if output_raw else Path.cwd() / "output"
        return ExportJob(
            mode=self.mode_var.get(),
            input_path=input_path,
            output_dir=output_dir,
            options=self._processing_options(),
            open_output_after_export=bool(self.open_after_export_var.get()),
            recursive=bool(self.recursive_var.get()),
        )

    def _preview_source(self, *_args: object) -> Path | None:
        raw = clean_path_text(self.input_var.get())
        if not raw:
            return None
        return resolve_preview_source(Path(raw).expanduser())

    def _refresh_preview(self, *_args: object) -> None:
        self.preview_token += 1
        token = self.preview_token
        self.after(200, lambda: self._start_preview(token))

    def _start_preview(self, token: int, *_args: object) -> None:
        if token != self.preview_token:
            return
        source = self._preview_source()
        if not source:
            self.input_preview_label.configure(text="Select a supported image or folder.", image="")
            self.output_preview_label.configure(text="Preview will appear here.", image="")
            return
        if self.preview_worker and self.preview_worker.is_alive():
            return

        try:
            with Image.open(source) as image:
                self.input_preview_ref = self._preview_photo(image.convert("RGBA"))
                self.input_preview_label.configure(image=self.input_preview_ref, text="")
        except OSError as exc:
            self.input_preview_label.configure(text=f"Input preview failed: {exc}", image="")
            return

        options = self._processing_options()
        self.preview_button.configure(state=tk.DISABLED)
        self.status_var.set("Rendering preview...")
        self.preview_worker = threading.Thread(
            target=self._preview_worker_fn, args=(source, token, options), daemon=True
        )
        self.preview_worker.start()

    def _preview_worker_fn(self, source: Path, token: int, options: ProcessingOptions) -> None:
        try:
            with Image.open(source) as image:
                processed = process_image_object(image, options)
            self.log_queue.put(("preview", token, processed))
        except Exception as exc:
            self.log_queue.put(("preview_error", token, str(exc)))

    def _preview_photo(self, image: Image.Image) -> ImageTk.PhotoImage:
        preview = image.copy()
        preview.thumbnail(PREVIEW_SIZE, Image.Resampling.LANCZOS)
        board = self._checkerboard(preview.size)
        board.alpha_composite(preview)
        return ImageTk.PhotoImage(board)

    def _checkerboard(self, size: tuple[int, int]) -> Image.Image:
        canvas = Image.new("RGBA", size, (210, 210, 210, 255))
        tile = 12
        for y in range(0, size[1], tile):
            for x in range(0, size[0], tile):
                if ((x // tile) + (y // tile)) % 2:
                    canvas.paste(
                        (245, 245, 245, 255),
                        (x, y, min(x + tile, size[0]), min(y + tile, size[1])),
                    )
        return canvas

    def _start_export(self, *_args: object) -> None:
        if self.export_worker and self.export_worker.is_alive():
            messagebox.showinfo("Busy", "Export is already running.")
            return
        job = self._current_job()
        if job is None:
            messagebox.showerror("Invalid input", "Select an existing supported input image or folder.")
            return
        if job.mode == "single" and not job.input_path.is_file():
            messagebox.showerror("Invalid input", "Single image mode needs an image file.")
            return
        if job.mode == "batch" and not job.input_path.is_dir():
            messagebox.showerror("Invalid input", "Batch folder mode needs an input folder.")
            return

        self._save_settings()
        self.cancel_export_event.clear()
        self.export_button.configure(state=tk.DISABLED)
        self.cancel_button.configure(state=tk.NORMAL)
        self.progress_var.set(0)
        self.progress_text_var.set("Preparing export...")
        self.export_summary_var.set("Export running...")
        self.status_var.set("Exporting...")
        self.export_worker = threading.Thread(target=self._export_worker_fn, args=(job,), daemon=True)
        self.export_worker.start()

    def _cancel_export(self, *_args: object) -> None:
        if self.export_worker and self.export_worker.is_alive():
            self.cancel_export_event.set()
            self.cancel_button.configure(state=tk.DISABLED)
            self.status_var.set("Cancel requested...")
            self.progress_text_var.set("Cancel requested; finishing current file safely.")
            self._log("CANCEL requested")

    def _export_worker_fn(self, job: ExportJob) -> None:
        canceled = False
        try:
            job.output_dir.mkdir(parents=True, exist_ok=True)
            total = self._count_job_inputs(job)
            self.log_queue.put(("export_started", total))

            def on_progress(message: str) -> None:
                self.log_queue.put(message)
                self.log_queue.put(("export_status", message))
                if message.startswith("Saved "):
                    self.log_queue.put(("export_step", message))

            if job.mode == "single":
                if self.cancel_export_event.is_set():
                    canceled = True
                else:
                    output_path = build_output_path(
                        job.input_path,
                        job.output_dir,
                        suffix=job.options.normalized_suffix(),
                        extension=job.options.output_format,
                        overwrite=job.options.overwrite,
                    )
                    result = process_single(job.input_path, output_path, job.options, on_progress=on_progress)
                    self.last_output_path = result.output_path
                    self.log_queue.put(f"EXPORTED {result.output_path} ({result.width}x{result.height})")
                    self.log_queue.put(("export_result", 1, 0, 0, ()))
            else:
                summary = process_directory(
                    job.input_path,
                    job.output_dir,
                    job.options,
                    recursive=job.recursive,
                    on_progress=on_progress,
                    should_cancel=self.cancel_export_event.is_set,
                )
                canceled = self.cancel_export_event.is_set()
                self.log_queue.put(
                    f"EXPORTED processed={summary.processed} failed={summary.failed} skipped={summary.skipped}"
                )
                self.log_queue.put(
                    ("export_result", summary.processed, summary.failed, summary.skipped, summary.errors)
                )
                if summary.results:
                    self.last_output_path = summary.results[-1].output_path

            if job.open_output_after_export and not canceled:
                self.log_queue.put(("open_output", str(job.output_dir)))
        except Exception as exc:
            self.log_queue.put(("export_error", str(exc)))
        finally:
            self.log_queue.put(("export_finished", canceled))

    def _count_job_inputs(self, job: ExportJob) -> int:
        if job.mode == "single":
            return 1
        if job.recursive:
            return len(
                [
                    child
                    for child in job.input_path.rglob("*")
                    if child.is_file() and child.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
                ]
            )
        return len(iter_images(job.input_path))

    def _drain_log_queue(self, *_args: object) -> None:
        try:
            while True:
                message = self.log_queue.get_nowait()
                if isinstance(message, tuple) and message[0] == "preview":
                    _, token, image = message
                    if token == self.preview_token:
                        self.output_preview_ref = self._preview_photo(image)
                        self.output_preview_label.configure(image=self.output_preview_ref, text="")
                        self.preview_button.configure(state=tk.NORMAL)
                        self.status_var.set("Preview ready")
                elif isinstance(message, tuple) and message[0] == "preview_error":
                    _, token, error = message
                    if token == self.preview_token:
                        self.output_preview_label.configure(text=str(error), image="")
                        self.preview_button.configure(state=tk.NORMAL)
                        self.status_var.set("Preview failed")
                        self._log(f"PREVIEW ERROR {error}")
                elif isinstance(message, tuple) and message[0] == "open_output":
                    self._open_folder_path(Path(str(message[1])))
                elif isinstance(message, tuple) and message[0] == "export_started":
                    self.export_total = max(0, int(message[1]))
                    self.export_done = 0
                    self.progress_var.set(0)
                    self.progress_text_var.set(f"Exporting 0/{self.export_total} file(s)...")
                elif isinstance(message, tuple) and message[0] == "export_status":
                    self.progress_text_var.set(str(message[1]))
                elif isinstance(message, tuple) and message[0] == "export_step":
                    self.export_done += 1
                    if self.export_total:
                        self.progress_var.set(min(100, (self.export_done / self.export_total) * 100))
                    else:
                        self.progress_var.set(100)
                    self.progress_text_var.set(
                        f"Exported {self.export_done}/{self.export_total} file(s). {message[1]}"
                    )
                elif isinstance(message, tuple) and message[0] == "export_result":
                    _, processed, failed, skipped, errors = message
                    self.export_summary_var.set(
                        f"Summary: processed={processed}, failed={failed}, skipped={skipped}"
                    )
                    for error in errors:
                        self._log(f"ERROR {error}")
                elif isinstance(message, tuple) and message[0] == "export_error":
                    self.export_summary_var.set(f"Export failed: {message[1]}")
                    self.status_var.set("Export failed")
                    self._log(f"ERROR {message[1]}")
                elif isinstance(message, tuple) and message[0] == "export_finished":
                    canceled = bool(message[1])
                    self.export_button.configure(state=tk.NORMAL)
                    self.cancel_button.configure(state=tk.DISABLED)
                    if canceled:
                        self.status_var.set("Export canceled")
                        self.progress_text_var.set("Export canceled.")
                    else:
                        self.status_var.set("Ready")
                        if self.export_total and self.progress_var.get() < 100:
                            self.progress_var.set(100)
                else:
                    self._log(str(message))
        except queue.Empty:
            pass
        self.after(100, self._drain_log_queue)

    def _open_folder_path(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def _open_output_folder(self, *_args: object) -> None:
        path = Path(clean_path_text(self.output_var.get()) or str(Path.cwd() / "output")).expanduser()
        self._open_folder_path(path)

    def _log(self, message: str) -> None:
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def _clear_log(self, *_args: object) -> None:
        self.log_text.delete("1.0", tk.END)

    def _settings_payload(self) -> dict[str, Any]:
        options = self._processing_options()
        return {
            "input_path": clean_path_text(self.input_var.get()),
            "output_dir": clean_path_text(self.output_var.get()),
            "mode": self.mode_var.get(),
            "selected_preset": self.preset_var.get(),
            "remove_background": options.remove_background,
            "rembg_model": options.rembg_model,
            "alpha_threshold": options.alpha_threshold,
            "feather_radius": options.feather_radius,
            "alpha_gamma": options.alpha_gamma,
            "despill_strength": options.despill_strength,
            "fit_mode": options.fit_mode,
            "canvas_width": self.width_var.get(),
            "canvas_height": self.height_var.get(),
            "output_format": options.output_format,
            "suffix": options.suffix,
            "overwrite": options.overwrite,
            "recursive": bool(self.recursive_var.get()),
            "open_output_after_export": bool(self.open_after_export_var.get()),
            "window_geometry": self.geometry(),
        }

    def _save_settings(self) -> None:
        try:
            save_json_object(settings_path(), self._settings_payload())
        except Exception as exc:
            self._log(f"WARN could not save GUI settings: {exc}")

    def _on_close(self) -> None:
        self._save_settings()
        self.destroy()


def main() -> None:
    app = AlphaDropperApp()
    app.mainloop()


if __name__ == "__main__":  # pragma: no cover
    main()
