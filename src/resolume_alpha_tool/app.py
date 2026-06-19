"""Tkinter desktop GUI for Resolume Alpha Dropper."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .core.batch import process_directory, process_single
from .core.models import ProcessingOptions
from .core.naming import build_output_path


class AlphaDropperApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Resolume Alpha Dropper")
        self.geometry("920x620")
        self.minsize(820, 560)
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.worker: threading.Thread | None = None

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(Path.cwd() / "output"))
        self.mode_var = tk.StringVar(value="single")
        self.remove_bg_var = tk.BooleanVar(value=True)
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

        self._build_ui()
        self.after(100, self._drain_log_queue)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(root, text="Resolume Alpha Dropper", font=("Segoe UI", 18, "bold"))
        title.pack(anchor="w")

        subtitle = ttk.Label(
            root,
            text="Local background removal + alpha cleanup + transparent export for Resolume assets.",
        )
        subtitle.pack(anchor="w", pady=(0, 12))

        top = ttk.Frame(root)
        top.pack(fill=tk.X, pady=6)

        ttk.Label(top, text="Mode").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(top, text="Single image", variable=self.mode_var, value="single").grid(
            row=0, column=1, sticky="w"
        )
        ttk.Radiobutton(top, text="Batch folder", variable=self.mode_var, value="batch").grid(
            row=0, column=2, sticky="w"
        )

        paths = ttk.LabelFrame(root, text="Paths", padding=10)
        paths.pack(fill=tk.X, pady=8)
        paths.columnconfigure(1, weight=1)

        ttk.Label(paths, text="Input").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(paths, textvariable=self.input_var).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Button(paths, text="Browse", command=self._browse_input).grid(row=0, column=2, padx=(8, 0))

        ttk.Label(paths, text="Output folder").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(paths, textvariable=self.output_var).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Button(paths, text="Browse", command=self._browse_output).grid(row=1, column=2, padx=(8, 0))

        options = ttk.LabelFrame(root, text="Processing", padding=10)
        options.pack(fill=tk.X, pady=8)
        for col in range(8):
            options.columnconfigure(col, weight=1)

        ttk.Checkbutton(options, text="Remove background", variable=self.remove_bg_var).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(options, text="Model").grid(row=0, column=2, sticky="e")
        ttk.Combobox(
            options,
            textvariable=self.model_var,
            values=["u2net", "u2netp", "isnet-general-use", "silueta", "birefnet-general"],
            width=18,
        ).grid(row=0, column=3, sticky="w")

        ttk.Label(options, text="Threshold").grid(row=1, column=0, sticky="w", pady=8)
        ttk.Spinbox(options, from_=0, to=255, textvariable=self.threshold_var, width=8).grid(
            row=1, column=1, sticky="w"
        )
        ttk.Label(options, text="Feather").grid(row=1, column=2, sticky="w")
        ttk.Spinbox(options, from_=0, to=10, increment=0.1, textvariable=self.feather_var, width=8).grid(
            row=1, column=3, sticky="w"
        )
        ttk.Label(options, text="Gamma").grid(row=1, column=4, sticky="w")
        ttk.Spinbox(options, from_=0.1, to=4, increment=0.1, textvariable=self.gamma_var, width=8).grid(
            row=1, column=5, sticky="w"
        )
        ttk.Label(options, text="Despill").grid(row=1, column=6, sticky="w")
        ttk.Spinbox(options, from_=0, to=1, increment=0.05, textvariable=self.despill_var, width=8).grid(
            row=1, column=7, sticky="w"
        )

        export = ttk.LabelFrame(root, text="Export", padding=10)
        export.pack(fill=tk.X, pady=8)
        ttk.Label(export, text="Fit").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            export,
            textvariable=self.fit_var,
            values=["none", "contain", "cover", "stretch"],
            width=12,
        ).grid(row=0, column=1, sticky="w", padx=(4, 18))
        ttk.Label(export, text="Width").grid(row=0, column=2, sticky="w")
        ttk.Spinbox(export, from_=1, to=16384, textvariable=self.width_var, width=8).grid(
            row=0, column=3, sticky="w", padx=(4, 18)
        )
        ttk.Label(export, text="Height").grid(row=0, column=4, sticky="w")
        ttk.Spinbox(export, from_=1, to=16384, textvariable=self.height_var, width=8).grid(
            row=0, column=5, sticky="w", padx=(4, 18)
        )
        ttk.Label(export, text="Format").grid(row=0, column=6, sticky="w")
        ttk.Combobox(export, textvariable=self.format_var, values=["png", "webp"], width=8).grid(
            row=0, column=7, sticky="w", padx=(4, 18)
        )
        ttk.Checkbutton(export, text="Overwrite", variable=self.overwrite_var).grid(
            row=0, column=8, sticky="w"
        )

        actions = ttk.Frame(root)
        actions.pack(fill=tk.X, pady=(8, 6))
        self.run_button = ttk.Button(actions, text="Process", command=self._start_processing)
        self.run_button.pack(side=tk.LEFT)
        ttk.Button(actions, text="Clear log", command=self._clear_log).pack(side=tk.LEFT, padx=8)

        logs = ttk.LabelFrame(root, text="Log", padding=8)
        logs.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(logs, height=12, wrap="word")
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _browse_input(self) -> None:
        if self.mode_var.get() == "single":
            selected = filedialog.askopenfilename(
                title="Select image",
                filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("All", "*.*")],
            )
        else:
            selected = filedialog.askdirectory(title="Select input folder")
        if selected:
            self.input_var.set(selected)

    def _browse_output(self) -> None:
        selected = filedialog.askdirectory(title="Select output folder")
        if selected:
            self.output_var.set(selected)

    def _options(self) -> ProcessingOptions:
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

    def _start_processing(self) -> None:
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Busy", "Processing is already running.")
            return
        if not self.input_var.get().strip():
            messagebox.showerror("Missing input", "Select an input image or folder.")
            return
        if not self.output_var.get().strip():
            messagebox.showerror("Missing output", "Select an output folder.")
            return

        self.run_button.configure(state=tk.DISABLED)
        self.worker = threading.Thread(target=self._process_worker, daemon=True)
        self.worker.start()

    def _process_worker(self) -> None:
        try:
            options = self._options()
            input_path = Path(self.input_var.get())
            output_dir = Path(self.output_var.get())
            output_dir.mkdir(parents=True, exist_ok=True)
            if self.mode_var.get() == "single":
                output_path = build_output_path(
                    input_path,
                    output_dir,
                    suffix=options.normalized_suffix(),
                    extension=options.output_format,
                    overwrite=options.overwrite,
                )
                result = process_single(
                    input_path, output_path, options, on_progress=self.log_queue.put
                )
                self.log_queue.put(f"DONE {result.output_path} ({result.width}x{result.height})")
            else:
                summary = process_directory(
                    input_path, output_dir, options, on_progress=self.log_queue.put
                )
                self.log_queue.put(
                    f"DONE processed={summary.processed} failed={summary.failed} skipped={summary.skipped}"
                )
        except Exception as exc:
            self.log_queue.put(f"ERROR {exc}")
        finally:
            self.log_queue.put("__ENABLE_BUTTON__")

    def _drain_log_queue(self) -> None:
        try:
            while True:
                message = self.log_queue.get_nowait()
                if message == "__ENABLE_BUTTON__":
                    self.run_button.configure(state=tk.NORMAL)
                else:
                    self._log(message)
        except queue.Empty:
            pass
        self.after(100, self._drain_log_queue)

    def _log(self, message: str) -> None:
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def _clear_log(self) -> None:
        self.log_text.delete("1.0", tk.END)


def main() -> None:
    app = AlphaDropperApp()
    app.mainloop()


if __name__ == "__main__":  # pragma: no cover
    main()
