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

    Write-Host ""
    Write-Host "==> $Label"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$AppName = "AlphaPngExporter"
$ReleaseRoot = Join-Path $Root "release"
$AppDir = Join-Path $ReleaseRoot $AppName
$ZipPath = Join-Path $ReleaseRoot "$($AppName)_Portable.zip"
$ManifestPath = Join-Path $ReleaseRoot "$($AppName)_Portable_manifest.json"

if (-not (Test-Path ".venv")) {
    Invoke-Checked "Create virtual environment" { py "-$PythonTag" -m venv .venv }
}

. .\.venv\Scripts\Activate.ps1

Invoke-Checked "Upgrade pip" { python -m pip install --upgrade pip }
Invoke-Checked "Install project extras" { python -m pip install -e ".[dev,rembg]" }

if (-not $SkipTests) {
    Invoke-Checked "Compile sources" { python -m compileall -q src tests }
    Invoke-Checked "Run ruff" { python -m ruff check . }
    Invoke-Checked "Run tests" { python -m pytest }
}

Invoke-Checked "Check rembg backend" { python -m resolume_alpha_tool.cli rembg-check --model u2netp }

Remove-Item -Recurse -Force "dist", "build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $AppDir -ErrorAction SilentlyContinue
Remove-Item -Force $ZipPath, $ManifestPath -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $AppDir | Out-Null
New-Item -ItemType Directory -Force (Join-Path $AppDir "output") | Out-Null

Invoke-Checked "Build executable" {
    python -m PyInstaller --noconfirm --clean --onefile --windowed `
        --name $AppName `
        --collect-all rembg `
        --collect-all onnxruntime `
        --collect-all pymatting `
        --collect-all skimage `
        --collect-all scipy `
        --collect-all numpy `
        src\resolume_alpha_tool\app.py
}

Copy-Item "dist\$AppName.exe" (Join-Path $AppDir "$AppName.exe") -Force
Copy-Item "README_STARTEN.txt" (Join-Path $AppDir "README_STARTEN.txt") -Force
Compress-Archive -Path (Join-Path $AppDir "*") -DestinationPath $ZipPath -Force

$ExePath = Join-Path $AppDir "$AppName.exe"
$Manifest = [ordered]@{
    app_name = $AppName
    generated_at = (Get-Date).ToString("o")
    git_commit = (git rev-parse HEAD)
    exe = [ordered]@{
        path = $ExePath
        sha256 = (Get-FileHash $ExePath -Algorithm SHA256).Hash
    }
    zip = [ordered]@{
        path = $ZipPath
        sha256 = (Get-FileHash $ZipPath -Algorithm SHA256).Hash
    }
}

$Manifest | ConvertTo-Json -Depth 8 | Set-Content -Path $ManifestPath -Encoding UTF8
Write-Host ""
Write-Host "Release package complete: $ZipPath"
Write-Host "Manifest: $ManifestPath"
