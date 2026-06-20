# Architecture

## Layers

```text
GUI / CLI
  -> queue scanner / report writer
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
- Queue preview and report writing stay in core helpers so GUI behavior is testable.

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
- processing explicit retry queues
- supporting safe cancel checks for GUI batch runs

### `batch_queue.py`

Responsible for:

- scanning planned single/batch exports
- marking canonical outputs that will be skipped
- extracting failed input paths from batch errors

### `export_report.py`

Responsible for:

- building JSON-serializable export reports
- writing timestamped export report files

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
