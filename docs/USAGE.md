# Usage Guide

## Recommended first workflow

1. Install Python 3.11, 3.12, 3.13, or standard CPython 3.14.
2. Install the tool with `pip install -e ".[dev,rembg]"`.
3. Run `alpha-png rembg-check` once before a real export.
4. Launch the GUI with `alpha-png-gui` or use the CLI examples below.
5. Export transparent PNGs into a normal asset folder and drag them into Resolume.

## Good Resolume export defaults

Use:

- Format: `png`
- Target: `resolume`
- Preset: `1080p`
- Fit: `contain`
- Edge profile: `normal`
- Canvas: `1920x1080`

For sharper logo-like assets, use `--edge-profile tight`.
For softer photo cutouts, use `--edge-profile soft`.

## CLI commands

### Single Resolume export

```powershell
alpha-png convert .\input\photo.jpg .\output --target resolume --preset 1080p --fit contain
```

### Single Shirt/Print export

`remove` is kept as a compatibility alias for `convert`.

```powershell
alpha-png remove .\input\photo.jpg .\output --target shirt-print --shirt-padding 96 --edge-profile tight
```

### 4K or square Resolume canvas

```powershell
alpha-png convert .\input\logo.png .\output --target resolume --preset 4k
alpha-png convert .\input\logo.png .\output --target resolume --preset square-1080
```

### Batch professional mode

```powershell
alpha-png batch .\input .\output --recursive --target resolume --target shirt-print --report .\output\batch-report.json
```

The batch command scans supported image formats, keeps stable folder-aware ordering, collects per-file failures instead of aborting the full run, and can write a JSON report for handoff or QA.

### Output Validation 2.0

Validate an already exported PNG against the selected target contract:

```powershell
alpha-png validate .\output\asset_resolume.png --target resolume --preset 1080p
alpha-png validate .\output\asset_shirt_print.png --target shirt-print
```

The validator checks PNG format, alpha transparency, target dimensions, visible alpha coverage, and suspicious alpha bounds.

### Backend and version checks

```powershell
alpha-png rembg-check
alpha-png version
```

## Important options

- `--model`: rembg model name. Defaults to `u2net`.
- `--preset`: Resolume canvas preset: `1080p`, `4k`, `square-1080`.
- `--fit`: Resolume fit mode: `contain`, `cover`, `stretch`.
- `--edge-profile`: alpha cleanup profile: `normal`, `soft`, `tight`, `grow`.
- `--shirt-padding`: transparent padding in pixels for shirt/print exports.
- `--overwrite`: replace an existing output file instead of using collision-safe naming.
- `--report`: JSON batch report path for batch mode.

## Troubleshooting

### `rembg is not installed`

Install the optional dependency:

```powershell
pip install -e ".[rembg]"
```

### First run is slow

`rembg` may download model files on first use. Later runs are faster.

### White or bright edge halos

Try a tighter edge profile:

```powershell
--edge-profile tight
```

### Hard jagged edges

Try a softer edge profile:

```powershell
--edge-profile soft
```
