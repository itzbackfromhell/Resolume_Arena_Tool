# Usage Guide

## Recommended first workflow

1. Install Python 3.11 or 3.12.
2. Install the tool with `pip install -e ".[rembg]"`.
3. Launch the GUI with `resolume-alpha-gui`.
4. Select an image or folder.
5. Export transparent PNGs into your Resolume asset folder.
6. Drag the generated PNGs into Resolume.

## Good Resolume export defaults

Use:

- Format: `png`
- Fit: `contain`
- Width: `1920`
- Height: `1080`
- Threshold: `8`
- Feather: `0.8`
- Despill: `0.35`

For sharper logo-like assets:

- Threshold: `32`
- Feather: `0`
- Despill: `0.15`

## CLI examples

Single image, no AI background removal, just alpha cleanup:

```powershell
resolume-alpha remove .\input\logo.png .\output --preset clean
```

Single image with local background removal:

```powershell
resolume-alpha remove .\input\photo.jpg .\output --remove-bg --preset resolume_1080p
```

Batch:

```powershell
resolume-alpha batch .\input .\output --remove-bg --preset resolume_1080p
```

Watch folder:

```powershell
resolume-alpha watch .\watch_in .\watch_out --remove-bg --preset resolume_1080p
```

## Resolume connectivity check

Enable the webserver in Resolume, then:

```powershell
resolume-alpha resolume --host 127.0.0.1 --port 8080
```

This only checks reachability. Automatic clip import/triggering is intentionally left as a later integration layer because composition layouts differ.

## Troubleshooting

### `rembg is not installed`

Install the optional dependency:

```powershell
pip install -e ".[rembg]"
```

### First run is slow

`rembg` downloads model files on first use. Later runs are faster.

### White/bright edge halos

Increase despill slightly:

```powershell
--despill 0.45
```

or try:

```powershell
--preset soft_edge
```

### Hard jagged edges

Increase feather slightly:

```powershell
--feather 1.2
```

### Logos look blurry

Use hard cut:

```powershell
--preset hard_cut
```
