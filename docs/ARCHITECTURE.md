# Architecture

## Layers

```text
GUI / CLI
  -> batch service
    -> alpha processor
      -> Pillow operations
      -> optional rembg background removal
      -> alpha cleanup and visual effects
  -> output naming / validation
  -> optional Resolume API client
```

## Design rules

- Core services must not import Tkinter.
- GUI must not implement image algorithms.
- Optional dependencies must fail with actionable messages.
- Background-removal sessions are cached to keep batch processing fast.
- Batch runs collect errors and continue.

## Main components

### `alpha_processor.py`

Responsible for:

- opening images
- optional rembg background removal
- alpha thresholding
- edge feathering
- alpha gamma
- despill
- invert alpha
- auto-crop and transparent padding
- outline / glow / shadow effects
- canvas fitting
- export

### `batch.py`

Responsible for:

- validating folders
- scanning images
- generating output names
- calling `process_file`
- collecting batch summary/errors
- supporting safe cancel checks for GUI batch runs

### `cli.py`

Thin command layer. Converts user args into `ProcessingOptions`.

### `app.py`

Tkinter desktop app. Runs preview and export work in background threads so the UI does not freeze.

### `resolume_api.py`

Generic local REST client. It is intentionally conservative for v0.1. Future versions can add version-specific endpoints.

## Future: Resolume deep integration

Potential additions:

- OSC trigger client.
- Local REST endpoint mapping for loading clips.
- WebSocket watcher for composition changes.
- Watched-folder export profiles.
- DXV/FFmpeg/Alley handoff helper.
