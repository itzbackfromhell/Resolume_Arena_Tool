# Resolume Alpha Dropper

**Resolume Alpha Dropper** is a local-first Windows-friendly tool for creating transparent image assets for Resolume Arena/Avenue workflows.

The current desktop GUI is intentionally simple:

```text
one image in
  -> local background removal
  -> transparent 1920x1080 PNG export
  -> drag/import into Resolume
```

The app does not patch, inject into, or modify Resolume. It only writes image files into a normal output folder.

## Current GUI scope

The GUI is the first clean user path and does exactly one job:

- select one image
- remove the background with the local `rembg` backend
- fit the result onto a transparent 1920x1080 canvas
- save a PNG with the `_resolume` suffix
- avoid overwriting existing files by using numbered collision-safe names

Advanced knobs, presets, batch queue, retry-failed, reports, and watch-folder controls are intentionally not exposed in the simplified GUI.

## Core and CLI scope

The repository still contains reusable core services and CLI commands for automation/power-user workflows:

- single-image processing
- batch folder processing
- watch-folder processing
- diagnostics
- rembg runtime check
- Resolume webserver healthcheck
- workflow profiles

## Install

```powershell
git clone https://github.com/itzbackfromhell/Resolume_Arena_Tool.git
cd Resolume_Arena_Tool
python -m pip install --upgrade pip
python -m pip install -e ".[dev,rembg]"
```

Minimal install without background removal support:

```powershell
python -m pip install -e .
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

The GUI depends on the optional local `rembg` backend for background removal. Check it with:

```powershell
python -m resolume_alpha_tool.cli rembg-check
```

The first run can take longer because the local model may need to load or download into the model cache.

## Useful CLI commands

Single image:

```powershell
python -m resolume_alpha_tool.cli remove input.jpg output --remove-bg --preset resolume_1080p
```

Batch folder:

```powershell
python -m resolume_alpha_tool.cli batch input output --remove-bg --preset resolume_1080p
```

Watch folder:

```powershell
python -m resolume_alpha_tool.cli watch input output --remove-bg --preset resolume_1080p
```

Diagnostics:

```powershell
python -m resolume_alpha_tool.cli diagnostics
```

## Tests and quality gates

```powershell
python -m compileall -q src tests
python -m ruff check .
python -m pytest
```

## GUI docs

See [docs/GUI.md](docs/GUI.md).
