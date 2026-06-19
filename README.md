# Resolume Alpha Dropper

**Resolume Alpha Dropper** is a local-first Windows-friendly toolkit for creating transparent image assets for Resolume Arena/Avenue workflows.

It removes backgrounds, cleans alpha edges, batch-processes folders, exports transparent PNG/WebP files, and can optionally talk to a local Resolume webserver endpoint. No paid cloud API is required.

## Core idea

```text
image/folder in
  -> local background removal
  -> alpha cleanup / edge feather / matte despill
  -> transparent export
  -> optional Resolume handoff folder or local API call
```

## Features

- Local processing pipeline for transparent PNG/WebP assets.
- Optional `rembg` backend for AI background removal.
- Alpha cleanup controls:
  - threshold
  - feather radius
  - gamma correction
  - matte/despill cleanup
  - transparent-pixel RGB cleanup
- Batch folder processing.
- Watch-folder mode for auto-processing new files.
- Tkinter desktop GUI with preview, presets, logs, and export settings.
- CLI for automation and power users.
- Optional local Resolume REST/Webserver client scaffold.
- CI, tests, docs, AGENTS.md, and build script included.

## No-cost stack

The default workflow is local:

- Python
- Pillow
- optional `rembg[cpu]`
- optional Resolume local webserver/OSC workflow later

`rembg` can run as a Python library, CLI, HTTP server, or Docker container. Its upstream documentation currently lists Python `>=3.11, <3.14` and supports CPU/GPU installation extras.

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

### 4. Launch GUI

```powershell
resolume-alpha-gui
```

or:

```powershell
python -m resolume_alpha_tool.app
```

### 5. Use CLI

Single image:

```powershell
resolume-alpha remove input.jpg output\input_alpha.png --remove-bg --preset clean
```

Batch folder:

```powershell
resolume-alpha batch input output --remove-bg --preset resolume_1080p
```

Watch folder:

```powershell
resolume-alpha watch input output --remove-bg --preset resolume_1080p
```

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
    config.py
    exceptions.py
    file_watcher.py
    models.py
    naming.py
    presets.py
    resolume_api.py
    validation.py
presets/defaults.json
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
python -m pytest
python -m ruff check .
```

## Roadmap

- v0.1: local alpha export, batch mode, GUI, CLI.
- v0.2: better preview UX, drag/drop support, preset editor.
- v0.3: Resolume API clip import helpers.
- v0.4: OSC triggering.
- v1.0: installer, signed builds, GPU presets, production performance profiles.

## License

MIT

