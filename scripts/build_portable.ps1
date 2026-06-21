param(
    [switch]$SkipTests,
    [string]$PythonTag = "3.14"
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

$ReleaseRoot = Join-Path $Root "release"
$AppDir = Join-Path $ReleaseRoot "ResolumeAlphaDropper"
$ZipPath = Join-Path $ReleaseRoot "ResolumeAlphaDropper_Portable.zip"

if (-not (Test-Path ".venv")) {
    Invoke-Checked "Create virtual environment" { py "-$PythonTag" -m venv .venv }
}

. .\.venv\Scripts\Activate.ps1

Invoke-Checked "Check Python ABI" {
    python -c "import sys, sysconfig; value=sysconfig.get_config_var('Py_GIL_DISABLED'); print(sys.executable); print(sys.version); print('Py_GIL_DISABLED=', value); raise SystemExit(1 if str(value).strip().lower() not in ('none', '0', 'false', '') else 0)"
}

Invoke-Checked "Upgrade pip" { python -m pip install --upgrade pip }
Invoke-Checked "Install project extras" { pip install -e ".[dev,rembg]" }

if (-not $SkipTests) {
    Invoke-Checked "Compile sources" { python -m compileall -q src tests }
    Invoke-Checked "Run ruff" { python -m ruff check . }
    Invoke-Checked "Run tests" { python -m pytest }
}

Invoke-Checked "Check required background-removal backend" { python -m resolume_alpha_tool.cli rembg-check }

Remove-Item -Recurse -Force "dist", "build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $AppDir -ErrorAction SilentlyContinue
Remove-Item -Force $ZipPath -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $AppDir | Out-Null
New-Item -ItemType Directory -Force (Join-Path $AppDir "output") | Out-Null

Invoke-Checked "Build PyInstaller executable" {
    python -m PyInstaller --noconfirm --clean --onefile --windowed `
        --name ResolumeAlphaDropper `
        --collect-all rembg `
        --collect-all onnxruntime `
        --collect-all pymatting `
        --collect-all skimage `
        --collect-all scipy `
        --collect-all numpy `
        src\resolume_alpha_tool\app.py
}

Copy-Item "dist\ResolumeAlphaDropper.exe" (Join-Path $AppDir "ResolumeAlphaDropper.exe") -Force
Copy-Item "README_STARTEN.txt" (Join-Path $AppDir "README_STARTEN.txt") -Force

Compress-Archive -Path (Join-Path $AppDir "*") -DestinationPath $ZipPath -Force
Write-Host "Portable build complete: $ZipPath"
