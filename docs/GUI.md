# GUI Workflow

Alpha PNG Exporter's desktop GUI is intentionally focused:

```text
image or folder in -> required local background removal -> transparent PNG out
```

The GUI does not modify Resolume, inject into Resolume, or require Resolume to be installed. It only creates transparent PNG files.

## Main single-image flow

1. Click **Choose image** and select one supported image.
2. Click **Choose folder** if you do not want to use the default `output` folder.
3. Pick **Resolume** or **Shirt/Print**.
4. Pick only the small safe options you need:
   - Resolume preset: `1080p`, `4k`, or `square_1080`
   - Fit: `contain`, `cover`, or `stretch`
   - Shirt padding: transparent pixels around the cropped motif
   - Edge cleanup: `normal`, `soft`, `tight`, or `grow`
   - Preview: checkerboard, black, white, or alpha matte
5. Click the convert button.

## Batch folder flow

1. Click **Choose folder** next to **Batch folder**.
2. Choose the output folder.
3. Pick the active export type, or enable **Batch both** to export Resolume and Shirt/Print files in one pass.
4. Enable **Recursive** only when you intentionally want subfolders scanned.
5. Click **Convert folder**.

Batch export never aborts the whole folder because one file fails. Each file/target pair is collected, and the final summary shows exported and failed counts.

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
- default canvas: 1920x1080
- optional presets: 3840x2160 and 1080x1080
- default fit mode: contain
- suffix: `_resolume`
- overwrite: disabled

### Shirt/Print

Use this for print-on-demand uploads:

- remove background: enabled and required
- output format: PNG
- tighter crop around the motif
- harder alpha edge than Resolume mode
- adjustable transparent padding around the motif
- no 1920x1080 video canvas
- suffix: `_shirt_print`
- overwrite: disabled

If the target filename already exists, the app uses the collision-safe naming helper and writes a numbered output instead of overwriting user files.

The export path refuses to save a final result when background removal is disabled, when no alpha channel is present, or when the alpha result is fully opaque/fully transparent. Resolume mode validates the selected canvas size.

## Preview and alpha checks

The GUI can preview against:

- checkerboard
- black
- white
- alpha matte

The status text reports the image dimensions, alpha range, estimated visible percentage, and a first warning when the alpha looks suspicious, such as fully opaque alpha, empty alpha, or a very tiny motif.

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
