# GUI Workflow

Resolume Alpha Dropper's desktop GUI is intentionally focused for the first usable app version:

```text
one image in -> local background removal -> transparent 1920x1080 PNG out
```

The GUI does not modify Resolume, inject into Resolume, or require Resolume to be installed. It only creates a transparent asset file that can be dragged/imported into Resolume Arena/Avenue.

## Main flow

1. Click **Choose image** and select exactly one supported image.
2. Click **Choose folder** if you do not want to use the default `output` folder.
3. Click **Convert image for Resolume**.
4. Drag/import the exported PNG into Resolume.

## Fixed GUI export settings

The GUI deliberately exposes no advanced knobs yet. Every GUI export uses the same deterministic Resolume-oriented settings:

- remove background: enabled
- output format: PNG
- canvas: 1920x1080
- fit mode: contain
- suffix: `_resolume`
- overwrite: disabled

If the target filename already exists, the app uses the collision-safe naming helper and writes a numbered output instead of overwriting user files.

## Background removal dependency

Background removal uses the optional local `rembg` backend. Install it before relying on the GUI:

```powershell
python -m pip install -e ".[rembg]"
```

Check the local model/runtime setup with:

```powershell
python -m resolume_alpha_tool.cli rembg-check
```

The first export can take longer because the local AI model may need to load or download into the local model cache.

## Supported input formats

- PNG
- JPG/JPEG
- WebP
- BMP
- TIFF

## What moved out of the GUI

Batch export, queue preview, retry-failed, presets, reports, watch-folder mode, and power-user export controls are not part of the simplified GUI anymore. The core services and CLI can still keep automation features while the desktop app stays focused on the first clean user path.
