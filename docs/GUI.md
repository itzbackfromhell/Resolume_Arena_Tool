# GUI Workflow

Alpha PNG Exporter's desktop GUI is intentionally focused:

```text
one image in -> required local background removal -> transparent PNG out
```

The GUI does not modify Resolume, inject into Resolume, or require Resolume to be installed. It only creates transparent PNG files.

## Main flow

1. Click **Choose image** and select exactly one supported image.
2. Click **Choose folder** if you do not want to use the default `output` folder.
3. Pick **Resolume** or **Shirt/Print**.
4. Click the convert button.

## Dark interface

The desktop UI uses a built-in black/neon theme by default:

- pure black root window and panels
- pure black text fields
- pure black preview placeholders
- dark black/green alpha checkerboard preview
- poison-green title and section headings
- poison-green accent buttons and selected controls

This is a fixed app theme, not an operating-system setting.

## Export modes

### Resolume

Use this for VJ/video workflows:

- remove background: enabled and required
- output format: PNG
- canvas: 1920x1080
- fit mode: contain
- suffix: `_resolume`
- overwrite: disabled

### Shirt/Print

Use this for print-on-demand uploads:

- remove background: enabled and required
- output format: PNG
- tighter crop around the motif
- harder alpha edge than Resolume mode
- transparent padding around the motif
- no 1920x1080 video canvas
- suffix: `_shirt_print`
- overwrite: disabled

If the target filename already exists, the app uses the collision-safe naming helper and writes a numbered output instead of overwriting user files.

The export path refuses to save a final result when background removal is disabled, when no alpha channel is present, or when the alpha result is fully opaque/fully transparent. Resolume mode additionally requires 1920x1080 output.

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
