# Architecture

## Layers

```text
GUI / CLI
  -> resource resolver / diagnostics
  -> queue scanner / report writer
  -> batch service / watch-folder service
    -> alpha processor
      -> Pillow operations
      -> optional rembg background removal
      -> alpha cleanup and visual effects
  -> output naming / validation
  -> safe Resolume workflow profiles
  -> optional Resolume API client
```

## Design rules

- Core services must not import Tkinter.
- GUI must not implement image algorithms.
- Optional dependencies must fail with actionable messages.
- Background-removal sessions are cached to keep batch processing fast.
- Batch runs collect errors and continue.
- Queue preview and report writing stay in core helpers so GUI behavior is testable.
- Portable builds must resolve resources in both source checkouts and PyInstaller executables.
- Resolume integration remains conservative: export assets safely, do not mutate Resolume projects blindly.

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

### `file_watcher.py`

Responsible for:

- polling a folder without a watchdog dependency
- processing only new or changed files
- respecting safe stop/cancel callbacks

### `resources.py`

Responsible for:

- resolving bundled resources in source and PyInstaller modes
- resolving portable writable folders
- creating expected `output/` and `logs/` folders

### `diagnostics.py`

Responsible for:

- collecting runtime/package/path diagnostics
- writing support JSON reports

### `resolume_profiles.py`

Responsible for:

- defining safe output-oriented Resolume workflow profiles
- avoiding unsafe Resolume project mutation

### `cli.py`

Thin command layer. Converts user args into `ProcessingOptions` and exposes healthcheck/profile/diagnostics commands.

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
