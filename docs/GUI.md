# GUI Workflow

Resolume Alpha Dropper's desktop GUI is intentionally focused:

```text
one image in -> required local background removal -> transparent 1920x1080 PNG out
```

The GUI does not modify Resolume, inject into Resolume, or require Resolume to be installed. It only creates a transparent PNG file that can be dragged/imported into Resolume Arena/Avenue.

## Main flow

1. Click **Choose image** and select exactly one supported image.
2. Click **Choose folder** if you do not want to use the default `output` folder.
3. Click **Convert image for Resolume**.
4. Drag/import the exported PNG into Resolume.

## Fixed GUI export settings

Every GUI export uses the same Resolume-oriented settings:

- remove background: enabled and required
- output format: PNG
- canvas: 1920x1080
- fit mode: contain
- suffix: `_resolume`
- overwrite: disabled

If the target filename already exists, the app uses the collision-safe naming helper and writes a numbered output instead of overwriting user files.

The export path refuses to save a final result when background removal is disabled, when the PNG is not 1920x1080, when no alpha channel is present, or when the alpha result is fully opaque/fully transparent.

## Background removal dependency

Background removal uses the required local `rembg` backend. Use a standard CPython x64 interpreter on Windows.

Do not use a free-threaded Windows build such as `Python314t` / `cp314t` for the rembg workflow. That ABI can fail dependency resolution for the onnxruntime stack.

Install the project with rembg from an activated venv:

```powershell
python -m pip install -e ".[dev,rembg]"
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
