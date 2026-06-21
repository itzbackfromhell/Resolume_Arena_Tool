param(
    [string]$ExePath = "release\AlphaPngExporter\AlphaPngExporter.exe"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ExePath)) {
    throw "Portable EXE not found: $ExePath"
}

$AppDir = Split-Path -Parent $ExePath
foreach ($Required in @("output", "README_STARTEN.txt")) {
    $Path = Join-Path $AppDir $Required
    if (-not (Test-Path $Path)) {
        throw "Portable artifact missing: $Path"
    }
}

Write-Host "Portable smoke passed: $AppDir"
