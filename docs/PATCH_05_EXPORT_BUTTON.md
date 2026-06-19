# Patch 5 - Explicit Export Button

Patch 5 makes the GUI export flow clearer.

## What changed

- The old **Process** action is now an explicit **Export** button.
- Export status text now says `Exporting...` instead of `Processing...`.
- Successful exports are logged as `EXPORTED ...`.
- Added an **Open folder after export** checkbox.
- If enabled, the app opens the selected output folder after exporting.
- The existing **Open output** button remains available for manual access.

## Usage

1. Select **File** or **Folder** under Input.
2. Choose an **Output folder**.
3. Pick export options.
4. Click **Export**.
5. The exported PNG/WebP is written into the selected output folder.

The app does not download files because it runs locally. Exported files are created directly on disk.
