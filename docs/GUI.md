# GUI Workflow

Resolume Alpha Dropper is a local desktop tool. It does not download exports from a server; it writes files directly to the selected output folder.

## Main flow

1. Choose **Single image** or **Batch folder**.
2. Select an input with **File** or **Folder**.
3. Choose an **Output folder**.
4. Choose or create a preset.
5. Adjust alpha cleanup, alpha effects, and export options.
6. Use **Preview** to check the processed result.
7. Click **Export**.

## Persistent GUI state

The GUI saves its last-used state when an export starts and when the window closes:

- input path
- output folder
- mode
- selected preset
- cleanup/effect/export values
- overwrite / recursive batch / open-folder settings
- window geometry

User settings are stored outside the repository in the per-user config directory.

## Presets

Bundled presets are loaded from `presets/defaults.json`.

The GUI also supports user presets:

- **Apply** loads the selected preset into the current controls.
- **Save Current** stores the current controls as a user preset.
- **Delete** removes user presets. Bundled presets are protected.
- **Import** loads a JSON preset file.
- **Export Selected** writes the active preset to a JSON file.

A user preset can shadow a bundled preset with the same name. Deleting the user preset reveals the bundled preset again.

## Alpha effects

The **Alpha effects** panel runs after alpha cleanup and before canvas fitting:

- **Invert alpha** flips the mask.
- **Auto-crop alpha** trims empty transparent bounds.
- **Padding** adds transparent space around the asset.
- **Outline** adds an outer stroke.
- **Glow** adds a blurred glow behind the asset.
- **Shadow** adds a blurred offset shadow.
- **Shadow X/Y** controls shadow offset.

Effect margins are added automatically so outline, glow, and shadow have room before final canvas fitting.

## Export behavior

- Single-image export writes one PNG/WebP into the output folder.
- Batch export writes one output file per supported image.
- **Recursive batch** includes supported images in nested folders.
- The progress bar updates as files are saved.
- **Cancel** requests a safe stop. The current file may finish before the batch stops.
- The summary line shows processed / failed / skipped counts after export.
- The log shows `EXPORTED ...` after successful exports.
- Enable **Open folder after export** to open Windows Explorer automatically after export.
- **Open output** can be used any time to open the selected output folder manually.

## Background removal

`Remove background` uses the optional local `rembg` backend. Test it separately before relying on the GUI:

```powershell
python -m resolume_alpha_tool.cli rembg-check
```

If the check fails, the issue is in the local `rembg`/`onnxruntime`/model-cache setup rather than the GUI export path.

## Supported input formats

- PNG
- JPG/JPEG
- WebP
- BMP
- TIFF

## Safety rule

The app does not modify Resolume binaries. It only creates transparent assets beside Resolume so they can be dragged/imported into Resolume Arena/Avenue.
