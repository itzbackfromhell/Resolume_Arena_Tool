# Resolume Alpha Dropper

**Resolume Alpha Dropper** is a local-first Windows desktop tool for creating one transparent PNG asset for Resolume Arena/Avenue from one normal image.

```text
one image in
  -> required local background removal with rembg
  -> transparent 1920x1080 PNG export
  -> drag/import into Resolume
```

The app does not patch, inject into, or modify Resolume. It only writes image files into a normal output folder.

## Important Python version note

For background removal on Windows, use a **standard CPython x64** install. Do **not** use the free-threaded Windows build such as `Python314t` / `cp314t` for the rembg workflow.

Check what interpreter PowerShell is using:

```powershell
py -0p
python -c "import sys, sysconfig; print(sys.executable); print(sys.version); print('Py_GIL_DISABLED=', sysconfig.get_config_var('Py_GIL_DISABLED'))"
```

If `Py_GIL_DISABLED` prints `1`, use another standard Python interpreter for this project.

## Current scope

The app does exactly one job:

- select one image
- remove the background with the local `rembg` backend
- fit the result onto a transparent 1920x1080 canvas
- save a PNG with the `_resolume` suffix
- avoid overwriting existing files by using numbered collision-safe names
- refuse exports when background removal is disabled, missing, or produces a fully opaque/empty alpha result

Batch export, queue preview, retry-failed, presets, reports, watch-folder mode, Resolume REST checks, and power-user export controls have been removed from the focused app path.

## Install

```powershell
git clone https://github.com/itzbackfromhell/Resolume_Arena_Tool.git
cd Resolume_Arena_Tool
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,rembg]"
```

## Launch GUI

```powershell
python -m resolume_alpha_tool.app
```

or, after installing console scripts:

```powershell
resolume-alpha-gui
```

## Verify background removal

```powershell
python -m resolume_alpha_tool.cli rembg-check
```

The first run can take longer because the local model may need to load or download into the model cache.

## CLI

Convert one image from PowerShell:

```powershell
python -m resolume_alpha_tool.cli convert input.jpg output
```

## Portable EXE build

```powershell
.\scripts\build_portable.ps1
```

The build script runs tests, checks the required `rembg` backend, and asks PyInstaller to collect the rembg/ONNX runtime packages.

## Tests and quality gates

```powershell
python -m compileall -q src tests
python -m ruff check .
python -m pytest
```

## GUI docs

See [docs/GUI.md](docs/GUI.md).
