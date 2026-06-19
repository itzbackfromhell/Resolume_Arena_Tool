# GUI v0.2 Workflow

Resolume Alpha Dropper now includes a stronger desktop workflow for local transparent asset creation.

## Included in this patch

- Preset buttons loaded from `presets/defaults.json`.
- Input preview for selected images.
- Processed preview on a checkerboard background.
- Batch preview using the first previewable image in the selected folder.
- Status text for ready, previewing, failed preview, and processing states.
- Safer default behavior: background removal is off by default because `rembg` is optional.

## Recommended usage

```powershell
cd D:\KI_STUFF\Resolume_Arena_Tool
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
resolume-alpha-gui
```

## Optional local background removal

Install the optional backend separately:

```powershell
python -m pip install -e ".[rembg]"
```

Then enable **Remove background** in the GUI.

## Notes

The app still does not modify Resolume binaries. It creates clean transparent PNG/WebP assets that can be dragged into Resolume or later handed off through the local Resolume integration layer.
