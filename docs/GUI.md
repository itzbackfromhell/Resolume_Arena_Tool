# GUI Workflow

Resolume Alpha Dropper is a local desktop tool. It does not download exports from a server; it writes files directly to the selected output folder.

## Main flow

1. Choose **Single image** or **Batch folder**.
2. Select an input with **File** or **Folder**.
3. Choose an **Output folder**.
4. Adjust alpha cleanup and export options.
5. Use **Preview** to check the processed result.
6. Click **Export**.

## Export behavior

- Single-image export writes one PNG/WebP into the output folder.
- Batch export writes one output file per supported image.
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
