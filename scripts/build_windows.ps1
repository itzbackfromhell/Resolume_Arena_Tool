$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    py -3.11 -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,rembg]"
python -m pytest
python -m PyInstaller --noconfirm --clean --onefile --windowed --name ResolumeAlphaDropper src\resolume_alpha_tool\app.py

Write-Host "Build complete: dist\ResolumeAlphaDropper.exe"
