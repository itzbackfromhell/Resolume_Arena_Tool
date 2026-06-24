# Architecture

## Current layers

```text
GUI / CLI
  -> core/resolume_export.py
    -> alpha_processor.py
      -> Pillow operations
      -> optional local rembg background removal
      -> alpha cleanup
      -> transparent PNG canvas fitting
    -> output_validation.py
      -> PNG, size, alpha, visible-content and bounds validation
    -> output naming / input validation
  -> core/batch_export.py
    -> folder discovery
    -> per-file failure collection
    -> optional JSON report via core/reporting.py
  -> core/gui_worker.py
    -> typed GUI worker messages
    -> worker success/error/finished lifecycle
    -> user-facing GUI error payload normalization
  -> core/settings.py
    -> typed AppSettings
    -> config paths and legacy migration compatibility
    -> JSON roundtrip and value sanitizing
  -> core/profiles.py
    -> named Resolume/print workflow profiles
    -> profile aliases and JSON normalization
    -> conversion into ProcessingOptions
```

## Design rules

- Core services must not import Tkinter.
- GUI must not implement image algorithms.
- Optional dependencies must fail with actionable messages.
- Background-removal sessions are cached for repeated exports.
- Resolume integration remains file-based and conservative: export assets safely, do not mutate Resolume projects.
- CLI and GUI must share the same processing contracts whenever possible.
- Batch jobs must be deterministic, reportable, and safe against partial failures.
- Worker threads must communicate with Tk only through queue-safe message payloads.
- Settings must be sanitized before they affect export behavior.
- Workflow profiles must stay thin presets over existing export contracts, not separate image pipelines.

## Main components

### `resolume_export.py`

Single-image export service used by GUI and CLI. It owns the fixed export contract:

- local background removal enabled
- transparent PNG output
- Resolume or Shirt/Print target options
- collision-safe output naming unless `overwrite=True`
- Output Validation 2.0 after save

### `alpha_processor.py`

Responsible for:

- opening images
- optional rembg background removal
- alpha thresholding
- edge feathering
- alpha gamma
- conservative despill
- erode/dilate edge cleanup profiles
- transparent-pixel RGB cleanup
- crop/pad operations
- canvas fitting
- PNG export

### `output_validation.py`

Responsible for:

- validating saved PNG files
- enforcing target size contracts
- rejecting empty or fully opaque alpha results
- calculating visible alpha coverage
- reporting alpha bounds and warnings

### `batch_export.py`

Responsible for:

- stable folder-aware image discovery
- recursive batch scans
- multiple export targets per source
- collecting failures without aborting the full batch
- optional JSON report handoff

### `reporting.py`

Responsible for stable JSON payloads for batch summaries. These reports are intended for QA, handoff, and future release/export automation.

### `gui_worker.py`

Small worker-message contract used to keep GUI background work predictable:

- `GuiWorkerMessage` dataclass for queue payloads
- helpers for progress, success, error, and finished messages
- legacy tuple coercion for gradual migration from older GUI queue code
- error payload normalization through the shared Error UX formatter
- tested worker lifecycle without needing real Tk windows or real threads

### `settings.py`

First-class app settings service:

- `AppSettings` dataclass with stable UI-facing keys
- config directory resolution with legacy app-folder compatibility
- JSON object load/save helpers
- sanitizer for target, preset, fit, preview, edge, padding, and boolean values
- compatibility wrapper kept in `gui_settings.py` for the current Tk app

### `profiles.py`

Named workflow profile service for repeatable exports:

- built-in profiles for Resolume 1080p, Resolume 4K, Resolume Square 1080, and Shirt/Print Clean
- alias resolution for common terms like `resolume`, `4k`, `square`, and `shirt`
- JSON-object normalization for future user-defined profiles
- user-profile merge helper that allows key-based overrides
- conversion from profile settings into the existing `ProcessingOptions` contract

### `app.py`

Tkinter desktop app. It selects one input file or batch folder, builds target processing options, and runs export services on a worker thread so the UI does not freeze.

### `cli.py`

Professional command layer for:

- `convert`
- `remove`
- `batch`
- `validate`
- `rembg-check`
- `version`

## Next architecture targets

- Split `app.py` into smaller `ui/` modules.
- Wire `app.py` fully onto `core/gui_worker.py` during the UI module split.
- Migrate `app.py` from raw settings dictionaries to typed `AppSettings`.
- Expose named workflow profiles in CLI and GUI flows.
- Add structured release automation.
- Expand preview pro tools without moving image algorithms into the UI.
