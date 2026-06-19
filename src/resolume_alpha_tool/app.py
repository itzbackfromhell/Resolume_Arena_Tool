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
from tkinter import filedialog, messagebox, ttk
from typing import Any

from PIL import Image, ImageTk

from .core.alpha_processor import process_image_object
from .core.batch import process_directory, process_single
from .core.input_resolver import SUPPORTED_IMAGE_SUFFIXES, clean_path_text, resolve_preview_source
from .core.models import ProcessingOptions
from .core.naming import build_output_path

IMAGE_FILETYPES = [("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("All", "*.*")]
PRESET_PATH = Path(__file__).resolve().parents[2] / "presets" / "defaults.json"
PREVIEW_SIZE = (340, 240)


@dataclass(frozen=True)
class ProcessingJob:
    mode: str
    input_path: Path
    output_dir: Path
    options: ProcessingOptions


class AlphaDropperApp(tk.Tk):
    """Desktop GUI with robust path input, safe preview snapshots, and batch export."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Resolume Alpha Dropper")
        self.geometry("1160x740")
        self.minsize(1020, 660)

        self.log_queue: queue.Queue[object] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.preview_worker: threading.Thread | None = None
        self.preview_token = 0
        self.presets = self._load_presets()
        self.input_preview_ref: ImageTk.PhotoImage | None = None
        self.output_preview_ref: ImageTk.PhotoImage | None = None
        self.last_output_path: Path | None = None

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(Path.cwd() / "output"))
        self.mode_var = tk.StringVar(value="single")
        self.remove_bg_var = tk.BooleanVar(value=False)
        self.model_var = tk.StringVar(value="u2net")
        self.threshold_var = tk.IntVar(value=8)
        self.feather_var = tk.DoubleVar(value=0.8)
        self.gamma_var = tk.DoubleVar(value=1.0)
        self.despill_var = tk.DoubleVar(value=0.35)
        self.fit_var = tk.StringVar(value="contain")
        self.width_var = tk.IntVar(value=1920)
        self.height_var = tk.IntVar(value=1080)
        self.format_var = tk.StringVar(value="png")
        self.overwrite_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready")
        self.input_status_var = tk.StringVar(value="No input selected.")

        self._build_ui()
        self._bind_preview_traces()
        self.after(100, self._drain_log_queue)

    def _load_presets(self) -> dict[str, dict[str, Any]]:
        try:
            with PRESET_PATH.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except OSError:
            return {}
        return data if isinstance(data, dict) else {}

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(0, weight=0)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Resolume Alpha Dropper", font=("Segoe UI", 18, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Local transparent asset prep for Resolume Arena/Avenue.").grid(row=1, column=0, sticky="w")
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
        ttk.Radiobutton(panel, text="Single image", variable=self.mode_var, value="single", command=self._on_input_changed).pack(side=tk.LEFT)
        ttk.Radiobutton(panel, text="Batch folder", variable=self.mode_var, value="batch", command=self._on_input_changed).pack(side=tk.LEFT, padx=(12, 0))

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
        ttk.Label(panel, textvariable=self.input_status_var, foreground="#555555", wraplength=500).grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 0))

    def _build_preset_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Presets", padding=10)
        panel.grid(row=2, column=0, sticky="ew", pady=8)
        names = list(self.presets) or ["clean", "hard_cut", "soft_edge", "resolume_1080p", "resolume_4k"]
        for index, name in enumerate(names):
            ttk.Button(panel, text=name.replace("_", " ").title(), command=lambda n=name: self._apply_preset(n)).grid(row=index // 2, column=index % 2, sticky="ew", padx=4, pady=3)
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)

    def _build_processing_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Processing", padding=10)
        panel.grid(row=3, column=0, sticky="ew", pady=8)
        for col in range(4):
            panel.columnconfigure(col, weight=1)

        ttk.Checkbutton(panel, text="Remove background", variable=self.remove_bg_var, command=self._refresh_preview).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        ttk.Label(panel, text="Model").grid(row=1, column=0, sticky="w")
        ttk.Combobox(panel, textvariable=self.model_var, values=["u2net", "u2netp", "isnet-general-use", "silueta", "birefnet-general"], width=18).grid(row=1, column=1, columnspan=3, sticky="ew")

        self._spin(panel, "Threshold", self.threshold_var, 0, 255, 1, 2, 0)
        self._spin(panel, "Feather", self.feather_var, 0, 10, 0.1, 2, 2)
        self._spin(panel, "Gamma", self.gamma_var, 0.1, 4, 0.1, 3, 0)
        self._spin(panel, "Despill", self.despill_var, 0, 1, 0.05, 3, 2)

    def _spin(self, parent: ttk.Frame, label: str, var: tk.Variable, start: float, stop: float, step: float, row: int, col: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", pady=4)
        ttk.Spinbox(parent, from_=start, to=stop, increment=step, textvariable=var, width=8, command=self._refresh_preview).grid(row=row, column=col + 1, sticky="w", pady=4)

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
        ttk.Checkbutton(panel, text="Overwrite", variable=self.overwrite_var).grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 0))

    def _build_action_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Actions", padding=10)
        panel.grid(row=5, column=0, sticky="ew", pady=8)
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)

        self.preview_button = ttk.Button(panel, text="Preview", command=self._refresh_preview)
        self.preview_button.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=3)
        self.run_button = ttk.Button(panel, text="Process", command=self._start_processing)
        self.run_button.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=3)
        ttk.Button(panel, text="Open output", command=self._open_output_folder).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=3)
        ttk.Button(panel, text="Clear log", command=self._clear_log).grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=3)

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
        for var in (self.threshold_var, self.feather_var, self.gamma_var, self.despill_var, self.fit_var, self.width_var, self.height_var, self.format_var):
            var.trace_add("write", lambda *_: self._refresh_preview())

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

    def _apply_preset(self, name: str, *_args: object) -> None:
        preset = self.presets.get(name)
        if not preset:
            self._log(f"WARN preset not found: {name}")
            return
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
        self.status_var.set(f"Preset loaded: {name}")
        self._refresh_preview()

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
        )

    def _current_job(self, *_args: object) -> ProcessingJob | None:
        input_raw = clean_path_text(self.input_var.get())
        output_raw = clean_path_text(self.output_var.get())
        if not input_raw:
            return None
        input_path = Path(input_raw).expanduser()
        if not input_path.exists():
            return None
        output_dir = Path(output_raw).expanduser() if output_raw else Path.cwd() / "output"
        return ProcessingJob(mode=self.mode_var.get(), input_path=input_path, output_dir=output_dir, options=self._processing_options())

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
        self.preview_worker = threading.Thread(target=self._preview_worker_fn, args=(source, token, options), daemon=True)
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
                    canvas.paste((245, 245, 245, 255), (x, y, min(x + tile, size[0]), min(y + tile, size[1])))
        return canvas

    def _start_processing(self, *_args: object) -> None:
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Busy", "Processing is already running.")
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

        self.run_button.configure(state=tk.DISABLED)
        self.status_var.set("Processing...")
        self.worker = threading.Thread(target=self._process_worker, args=(job,), daemon=True)
        self.worker.start()

    def _process_worker(self, job: ProcessingJob) -> None:
        try:
            job.output_dir.mkdir(parents=True, exist_ok=True)
            if job.mode == "single":
                output_path = build_output_path(job.input_path, job.output_dir, suffix=job.options.normalized_suffix(), extension=job.options.output_format, overwrite=job.options.overwrite)
                result = process_single(job.input_path, output_path, job.options, on_progress=self.log_queue.put)
                self.last_output_path = result.output_path
                self.log_queue.put(f"DONE {result.output_path} ({result.width}x{result.height})")
            else:
                summary = process_directory(job.input_path, job.output_dir, job.options, on_progress=self.log_queue.put)
                self.log_queue.put(f"DONE processed={summary.processed} failed={summary.failed} skipped={summary.skipped}")
        except Exception as exc:
            self.log_queue.put(f"ERROR {exc}")
        finally:
            self.log_queue.put("enable_button")

    def _drain_log_queue(self, *_args: object) -> None:
        try:
            while True:
                message = self.log_queue.get_nowait()
                if message == "enable_button":
                    self.run_button.configure(state=tk.NORMAL)
                    self.status_var.set("Ready")
                elif isinstance(message, tuple) and message[0] == "preview":
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
                else:
                    self._log(str(message))
        except queue.Empty:
            pass
        self.after(100, self._drain_log_queue)

    def _open_output_folder(self, *_args: object) -> None:
        path = Path(clean_path_text(self.output_var.get()) or str(Path.cwd() / "output")).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def _log(self, message: str) -> None:
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def _clear_log(self, *_args: object) -> None:
        self.log_text.delete("1.0", tk.END)


def main() -> None:
    app = AlphaDropperApp()
    app.mainloop()


if __name__ == "__main__":  # pragma: no cover
    main()
