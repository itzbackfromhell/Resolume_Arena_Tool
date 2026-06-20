param(
    [ValidateSet("Light", "Full")]
    [string]$Flavor = "Light",
    [switch]$SkipTests
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
$ZipName = if ($Flavor -eq "Full") { "ResolumeAlphaDropper_Full_Portable.zip" } else { "ResolumeAlphaDropper_Light_Portable.zip" }
$ZipPath = Join-Path $ReleaseRoot $ZipName
$Extras = if ($Flavor -eq "Full") { ".[dev,rembg]" } else { ".[dev]" }

if (-not (Test-Path ".venv")) {
    Invoke-Checked "Create virtual environment" { py -3.11 -m venv .venv }
}

. .\.venv\Scripts\Activate.ps1
Invoke-Checked "Upgrade pip" { python -m pip install --upgrade pip }
Invoke-Checked "Install project extras" { pip install -e $Extras }

if (-not $SkipTests) {
    Invoke-Checked "Compile sources" { python -m compileall -q src tests }
    Invoke-Checked "Run tests" { python -m pytest }
    Invoke-Checked "Run ruff" { python -m ruff check . }
}

Remove-Item -Recurse -Force "dist", "build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $AppDir -ErrorAction SilentlyContinue
Remove-Item -Force $ZipPath -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $AppDir | Out-Null
New-Item -ItemType Directory -Force (Join-Path $AppDir "presets") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $AppDir "output") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $AppDir "logs") | Out-Null

Invoke-Checked "Build PyInstaller executable" {
    python -m PyInstaller --noconfirm --clean --onefile --windowed `
        --name ResolumeAlphaDropper `
        --add-data "presets;presets" `
        src\resolume_alpha_tool\app.py
}

Copy-Item "dist\ResolumeAlphaDropper.exe" (Join-Path $AppDir "ResolumeAlphaDropper.exe") -Force
Copy-Item "presets\defaults.json" (Join-Path $AppDir "presets\defaults.json") -Force
Copy-Item "README_STARTEN.txt" (Join-Path $AppDir "README_STARTEN.txt") -Force

Compress-Archive -Path (Join-Path $AppDir "*") -DestinationPath $ZipPath -Force
Write-Host "Portable build complete: $ZipPath"
