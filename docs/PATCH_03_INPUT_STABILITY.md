# Patch 3 - Input Stability

Patch 3 fixes the unstable GUI input workflow introduced by the first preview UI pass.

## What changed

- Split input selection into explicit **File** and **Folder** buttons.
- Added path cleanup for quoted/pasted paths.
- Added a tested `core.input_resolver` helper.
- Added input status text below the path fields.
- Added safer single-image vs batch-folder validation before processing.
- Moved preview/processing option reads onto the GUI thread before worker threads start.
- Kept background removal disabled by default because `rembg` remains optional.
- Added an **Open output** button.

## Why

Tkinter variables must not be read from background worker threads. Patch 3 snapshots paths and processing options on the main GUI thread, then passes immutable data into preview and processing workers.

## Local validation

```powershell
cd D:\KI_STUFF\Resolume_Arena_Tool
git pull
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m compileall -q src tests
python -m pytest
resolume-alpha-gui
```
