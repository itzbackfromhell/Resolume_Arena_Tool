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
```

## Design rules

- Core services must not import Tkinter.
- GUI must not implement image algorithms.
- Optional dependencies must fail with actionable messages.
- Background-removal sessions are cached for repeated exports.
- Resolume integration remains file-based and conservative: export assets safely, do not mutate Resolume projects.
- CLI and GUI must share the same processing contracts whenever possible.
- Batch jobs must be deterministic, reportable, and safe against partial failures.

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
- Add a first-class settings service shared by CLI and GUI.
- Add named Resolume workflow profiles.
- Add structured release automation.
- Expand preview pro tools without moving image algorithms into the UI.
