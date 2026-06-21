"""Focused Tkinter GUI for one background-removed alpha image export."""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from .core.gui_settings import load_json_object, save_json_object, settings_path
from .core.input_resolver import SUPPORTED_IMAGE_SUFFIXES, clean_path_text
from .core.models import ExportTarget, ProcessResult
from .core.resolume_export import (
    RESOLUME_CANVAS_SIZE,
    RESOLUME_OUTPUT_FORMAT,
    RESOLUME_OUTPUT_SUFFIX,
    SHIRT_PRINT_OUTPUT_SUFFIX,
    ExportJob,
    export_alpha_image,
    normalize_export_target,
    processing_options_for_target,
    resolume_processing_options,
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
    "resolume": "Resolume 1920x1080",
    "shirt_print": "Shirt/Print transparent PNG",
}


class AlphaDropperApp(tk.Tk):
    """Minimal desktop GUI: one image in, one transparent PNG out."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Alpha PNG Exporter")
        self.geometry("900x690")
        self.minsize(800, 620)

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
        self.output_var = tk.StringVar(value=str(self.settings.get("output_dir", Path.cwd() / "output")))
        self.export_target_var = tk.StringVar(value=normalized_target)
        self.status_var = tk.StringVar(value="Ready")
        self.input_status_var = tk.StringVar(value="No input selected.")
        self.result_var = tk.StringVar(value="Select one image and choose an export type.")
        self.mode_help_var = tk.StringVar(value="")

        self._build_ui()
        self._bind_events()
        self._update_input_status()
        self._update_mode_help()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._drain_messages)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=14)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(2, weight=1)

        ttk.Label(root, text="Alpha PNG Exporter", font=("Segoe UI", 18, "bold")).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
        )
        ttk.Label(
            root,
            text="One image -> required background removal -> transparent PNG for Resolume or shirt/print upload.",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))
        ttk.Label(root, textvariable=self.status_var).grid(row=0, column=1, sticky="e")

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

        self.input_preview_label = ttk.Label(input_box, text="Select an image.", anchor="center")
        self.input_preview_label.grid(row=0, column=0, sticky="nsew")
        self.output_preview_label = ttk.Label(output_box, text="Export result appears here.", anchor="center")
        self.output_preview_label.grid(row=0, column=0, sticky="nsew")

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

        ttk.Label(panel, text="Output folder").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(panel, textvariable=self.output_var).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Button(panel, text="Choose folder", command=self._browse_output).grid(
            row=1,
            column=2,
            sticky="ew",
            padx=(8, 0),
        )

        ttk.Label(panel, textvariable=self.input_status_var, foreground="#555555").grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(6, 0),
        )

    def _build_mode_panel(self, root: ttk.Frame) -> None:
        panel = ttk.LabelFrame(root, text="Export type", padding=10)
        panel.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        panel.columnconfigure(2, weight=1)

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
        ttk.Label(panel, textvariable=self.mode_help_var, foreground="#555555", wraplength=650).grid(
            row=0,
            column=2,
            sticky="w",
        )

    def _build_action_panel(self, root: ttk.Frame) -> None:
        panel = ttk.Frame(root)
        panel.grid(row=5, column=0, columnspan=2, sticky="ew")
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)

        self.export_button = ttk.Button(
            panel,
            text="Convert image",
            command=self._start_export,
        )
        self.export_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(panel, text="Open output folder", command=self._open_output_folder).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(6, 0),
        )
        ttk.Label(panel, textvariable=self.result_var, foreground="#555555", wraplength=820).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 0),
        )

    def _bind_events(self) -> None:
        self.input_var.trace_add("write", lambda *_: self._update_input_status())
        self.export_target_var.trace_add("write", lambda *_: self._update_mode_help())
        self.input_entry.bind("<Return>", lambda *_: self._update_input_status())
        self.input_entry.bind("<FocusOut>", lambda *_: self._update_input_status())

    def _browse_input(self) -> None:
        selected = filedialog.askopenfilename(title="Select one image", filetypes=IMAGE_FILETYPES)
        if selected:
            self.input_var.set(selected)

    def _browse_output(self) -> None:
        selected = filedialog.askdirectory(title="Select output folder")
        if selected:
            self.output_var.set(selected)

    def _input_path(self) -> Path | None:
        raw = clean_path_text(self.input_var.get())
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

    def _update_mode_help(self) -> None:
        target = self._export_target()
        if target == "shirt_print":
            self.mode_help_var.set(
                "Transparent PNG for print shops: tighter crop, harder alpha edge, padded motif, no 1920x1080 canvas."
            )
            button_text = "Convert for Shirt/Print"
        else:
            self.mode_help_var.set("Transparent 1920x1080 PNG for Resolume Arena/Avenue visuals.")
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
        self.input_status_var.set(f"Ready: {path.name}")
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
        except Exception as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        job = ExportJob(input_path=source, output_dir=self._output_dir(), target=target)
        self._save_settings()
        self.export_button.configure(state=tk.DISABLED)
        label = TARGET_LABELS[job.target]
        self.status_var.set("Exporting...")
        self.result_var.set(f"Removing background and writing {label}...")
        self.worker = threading.Thread(target=self._export_worker_fn, args=(job,), daemon=True)
        self.worker.start()

    def _export_worker_fn(self, job: ExportJob) -> None:
        try:
            result = export_alpha_image(job.input_path, job.output_dir, target=job.target, model=job.model)
            self.messages.put(("export_success", result))
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
                if kind == "export_success" and isinstance(payload, ProcessResult):
                    self._handle_export_success(payload)
                elif kind == "export_error":
                    self.status_var.set("Export failed")
                    self.result_var.set(f"Export failed: {payload}")
                elif kind == "export_finished":
                    self.export_button.configure(state=tk.NORMAL)
                    self._update_mode_help()
                    if self.status_var.get() == "Exporting...":
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

    def _load_preview(self, path: Path, *, target: str) -> None:
        try:
            with Image.open(path) as image:
                photo = self._preview_photo(image.convert("RGBA"))
        except OSError as exc:
            label = self.input_preview_label if target == "input" else self.output_preview_label
            label.configure(text=f"Preview failed: {exc}", image="")
            return

        if target == "input":
            self.input_preview_ref = photo
            self.input_preview_label.configure(image=self.input_preview_ref, text="")
        else:
            self.output_preview_ref = photo
            self.output_preview_label.configure(image=self.output_preview_ref, text="")

    def _preview_photo(self, image: Image.Image) -> ImageTk.PhotoImage:
        preview = image.copy()
        preview.thumbnail(PREVIEW_SIZE, Image.Resampling.LANCZOS)
        board = self._checkerboard(preview.size)
        board.alpha_composite(preview.convert("RGBA"))
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

    def _settings_payload(self) -> dict[str, str]:
        return {
            "input_path": clean_path_text(self.input_var.get()),
            "output_dir": clean_path_text(self.output_var.get()),
            "export_target": self.export_target_var.get(),
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
