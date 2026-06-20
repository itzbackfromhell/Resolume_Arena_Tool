param(
    [switch]$Full
)

$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [string]$Label,
        [scriptblock]$Command
    )

    Write-Host "==> $Label"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Test-Path ".venv")) {
    Invoke-Checked "Create virtual environment" { py -3.11 -m venv .venv }
}

. .\.venv\Scripts\Activate.ps1
Invoke-Checked "Upgrade pip" { python -m pip install --upgrade pip }
$Extras = if ($Full) { ".[dev,rembg]" } else { ".[dev]" }
Invoke-Checked "Install project extras" { pip install -e $Extras }
Invoke-Checked "Compile sources" { python -m compileall -q src tests }
Invoke-Checked "Run tests" { python -m pytest }
Invoke-Checked "Run ruff" { python -m ruff check . }
Invoke-Checked "Build PyInstaller executable" { python -m PyInstaller --noconfirm --clean --onefile --windowed --name ResolumeAlphaDropper --add-data "presets;presets" src\resolume_alpha_tool\app.py }

Write-Host "Build complete: dist\ResolumeAlphaDropper.exe"
