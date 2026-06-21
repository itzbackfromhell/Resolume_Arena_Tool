# Alpha PNG Exporter

**Alpha PNG Exporter** is a local-first Windows desktop tool for creating transparent PNG assets from one normal image.

```text
one image in
  -> required local background removal with rembg
  -> transparent PNG export for Resolume or shirt/print upload
```

The app does not patch, inject into, or modify Resolume. It only writes image files into a normal output folder.

## Export modes

### Resolume

- transparent PNG
- 1920x1080 canvas
- `contain` fit mode
- `_resolume` suffix
- optimized for Resolume Arena/Avenue visual workflows

### Shirt/Print

- transparent PNG
- tighter crop around the motif
- harder alpha edge than the Resolume mode
- transparent padding around the motif
- no 1920x1080 video canvas
- `_shirt_print` suffix
- intended for upload to print-on-demand sites such as shirt/product editors

The tool refuses exports when background removal is disabled, missing, or produces a fully opaque/empty alpha result.

## Important Python version note

For background removal on Windows, use a **standard CPython x64** install. Do **not** use the free-threaded Windows build such as `Python314t` / `cp314t` for the rembg workflow.

Check what interpreter PowerShell is using:

```powershell
py -0p
python -c "import sys, sysconfig; print(sys.executable); print(sys.version); print('Py_GIL_DISABLED=', sysconfig.get_config_var('Py_GIL_DISABLED'))"
```

If `Py_GIL_DISABLED` prints `1`, use another standard Python interpreter for this project.

## Install

```powershell
git clone https://github.com/itzbackfromhell/Resolume_Arena_Tool.git
cd Resolume_Arena_Tool
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,rembg]"
```

## One-command local verification

Run all local gates and the required rembg backend probe:

```powershell
.\scripts\verify_local.ps1
```

If the virtual environment is stale, broken, or was created with the wrong interpreter:

```powershell
.\scripts\verify_local.ps1 -RecreateVenv
```

Run all gates and then launch the GUI:

```powershell
.\scripts\verify_local.ps1 -LaunchApp
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

The first run can take longer because the local model may need to load or download into the model cache. The check imports rembg, creates the model session, and runs a tiny background-removal probe so failures show up before using the GUI.

## CLI

Resolume export:

```powershell
python -m resolume_alpha_tool.cli convert input.jpg output --target resolume
```

Shirt/print export:

```powershell
python -m resolume_alpha_tool.cli convert input.jpg output --target shirt-print
```

## Portable EXE build

```powershell
.\scripts\build_portable.ps1
```

The build script runs tests, checks the required `rembg` backend, asks PyInstaller to collect the rembg/ONNX runtime packages, and writes these artifacts:

```text
release/AlphaPngExporter/AlphaPngExporter.exe
release/AlphaPngExporter_Portable.zip
```

## Tests and quality gates

```powershell
python -m compileall -q src tests
python -m ruff check .
python -m pytest
python -m resolume_alpha_tool.cli rembg-check
```

## GUI docs

See [docs/GUI.md](docs/GUI.md).
