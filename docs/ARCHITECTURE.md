# Architecture

## Current layers

```text
GUI / tiny CLI
  -> core/resolume_export.py
    -> alpha_processor.py
      -> Pillow operations
      -> optional local rembg background removal
      -> alpha cleanup
      -> transparent 1920x1080 PNG canvas fitting
    -> output naming / input validation
```

## Design rules

- Core services must not import Tkinter.
- GUI must not implement image algorithms.
- Optional dependencies must fail with actionable messages.
- Background-removal sessions are cached for repeated exports.
- The default path is intentionally narrow: one image in, one Resolume-ready PNG out.
- Resolume integration remains file-based and conservative: export assets safely, do not mutate Resolume projects.

## Main components

### `resolume_export.py`

Single service used by GUI and CLI. It owns the fixed export contract:

- local background removal enabled
- transparent PNG output
- 1920x1080 canvas
- `_resolume` suffix
- collision-safe output naming

### `alpha_processor.py`

Responsible for:

- opening images
- optional rembg background removal
- alpha thresholding
- edge feathering
- alpha gamma
- conservative despill
- transparent-pixel RGB cleanup
- 1920x1080 canvas fitting
- PNG export

### `app.py`

Thin Tkinter desktop app. It selects one input file and one output folder, then runs the export service on a worker thread so the UI does not freeze.

### `cli.py`

Tiny command layer for `convert` and `rembg-check` only.

## Deliberately removed from current scope

- batch folder processing
- queue preview
- retry-failed exports
- user/bundled presets
- JSON export reports
- watch-folder processing
- Resolume REST/webserver client
- workflow profiles
- WebP/effects/sticker controls
