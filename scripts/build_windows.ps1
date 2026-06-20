param(
    [switch]$Full
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Test-Path ".venv")) {
    py -3.11 -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
$Extras = if ($Full) { ".[dev,rembg]" } else { ".[dev]" }
pip install -e $Extras
python -m compileall -q src tests
python -m pytest
python -m ruff check .
python -m PyInstaller --noconfirm --clean --onefile --windowed --name ResolumeAlphaDropper --add-data "presets;presets" src\resolume_alpha_tool\app.py

Write-Host "Build complete: dist\ResolumeAlphaDropper.exe"
