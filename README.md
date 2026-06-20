# Resolume Alpha Dropper

**Resolume Alpha Dropper** is a local-first Windows-friendly toolkit for creating transparent image assets for Resolume Arena/Avenue workflows.

It removes backgrounds, cleans alpha edges, adds visual alpha effects, batch-processes folders, exports transparent PNG/WebP files, and can optionally talk to a local Resolume webserver endpoint. No paid cloud API is required.

## Core idea

```text
image/folder in
  -> optional local background removal
  -> alpha cleanup / edge feather / matte despill
  -> optional alpha effects: crop / padding / outline / glow / shadow
  -> transparent PNG/WebP export
  -> drag/import into Resolume
```

## Features

- Tkinter desktop GUI with input preview, processed preview, presets, logs, progress, cancel, and explicit **Export** action.
- GUI state persistence for last-used paths, settings, selected preset, and window geometry.
- User preset manager with save, delete, import, and export support.
- Local processing pipeline for transparent PNG/WebP assets.
- Optional `rembg` backend for AI background removal.
- Alpha cleanup controls:
  - threshold
  - feather radius
  - gamma correction
  - matte/despill cleanup
  - transparent-pixel RGB cleanup
- Alpha effect controls:
  - invert alpha
  - auto-crop
  - transparent padding
  - outline
  - glow
  - shadow with X/Y offset
- Batch folder processing, including optional recursive batch mode in the GUI.
- Watch-folder mode for auto-processing new files.
- CLI for automation and power users.
- `rembg-check` command for local background-removal diagnostics.
- Optional local Resolume REST/Webserver client scaffold.
- CI, tests, docs, AGENTS.md, and build script included.

## No-cost stack

The default workflow is local:

- Python
- Pillow
- optional `rembg[cpu]`
- optional Resolume local webserver/OSC workflow later

`rembg` is optional and may depend on your Python, `onnxruntime`, and model-cache setup. Use `resolume-alpha rembg-check` to verify the local backend before using background removal in the GUI.

## Quick start

### 1. Clone

```powershell
git clone https://github.com/itzbackfromhell/Resolume_Arena_Tool.git
cd Resolume_Arena_Tool
```

### 2. Create venv

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### 3. Install

Minimal install:

```powershell
pip install -e .
```

With local background removal:

```powershell
pip install -e ".[rembg]"
```

With developer tooling:

```powershell
pip install -e ".[dev]"
```

Recommended local dev install:

```powershell
pip install -e ".[dev,rembg]"
```

### 4. Launch GUI

```powershell
resolume-alpha-gui
```

or directly from source:

```powershell
python -m resolume_alpha_tool.app
```

### 5. Use CLI

Check background-removal backend:

```powershell
resolume-alpha rembg-check
```

Single image:

```powershell
resolume-alpha remove input.jpg output --remove-bg --preset clean --overwrite
```

Single image with effects:

```powershell
resolume-alpha remove input.png output --preset sticker_outline --auto-crop --padding 48 --outline 8
```

Batch folder:

```powershell
resolume-alpha batch input output --remove-bg --preset resolume_1080p
```

Watch folder:

```powershell
resolume-alpha watch input output --remove-bg --preset resolume_1080p
```

## GUI workflow

See [docs/GUI.md](docs/GUI.md).

Short version:

1. Select **File** or **Folder** input.
2. Choose an **Output folder**.
3. Pick or save a preset.
4. Adjust cleanup/effect/export settings.
5. Use **Preview**.
6. Click **Export**.
7. Check progress and final summary.
8. Import/drag the exported PNG/WebP into Resolume.

## Resolume workflow

Recommended first workflow:

1. Export transparent PNGs into a dedicated folder, for example:

   ```text
   D:\ResolumeAssets\AlphaDropper
   ```

2. Drag/drop those files into Resolume Arena.
3. Later enable Resolume's local webserver and wire the client integration.

The app intentionally does **not** patch, modify, crack, or hook Resolume binaries. It creates clean alpha assets beside Resolume.

## Project structure

```text
src/resolume_alpha_tool/
  app.py              # Tkinter GUI
  cli.py              # CLI entrypoint
  core/
    alpha_processor.py
    batch.py
    exceptions.py
    file_watcher.py
    gui_settings.py
    input_resolver.py
    models.py
    naming.py
    preset_store.py
    presets.py
    rembg_runtime.py
    resolume_api.py
    validation.py
presets/defaults.json
docs/GUI.md
docs/USAGE.md
docs/ARCHITECTURE.md
tests/
scripts/build_windows.ps1
```

## Build Windows EXE

```powershell
.\scripts\build_windows.ps1
```

The script installs PyInstaller if needed and outputs a single-file executable under `dist/`.

## Quality gates

```powershell
python -m compileall -q src tests
python -m pytest
python -m ruff check .
```

## Roadmap

- v0.1: local alpha export, batch mode, GUI, CLI.
- v0.2: preview UX, explicit export flow, input stability, rembg diagnostics.
- v0.3: preset editor and stronger GUI packaging.
- v0.4: Resolume API clip import helpers.
- v1.0: installer, signed builds, GPU presets, production performance profiles.

## License

MIT
