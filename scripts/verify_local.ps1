param(
    [switch]$LaunchApp,
    [switch]$RecreateVenv,
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

if ($RecreateVenv -and (Test-Path ".venv")) {
    Remove-Item -Recurse -Force ".venv"
}

if (-not (Test-Path ".venv")) {
    Invoke-Checked "Create virtual environment" { py "-$PythonTag" -m venv .venv }
}

. .\.venv\Scripts\Activate.ps1

Invoke-Checked "Check Python ABI" {
    python -c "import sys, sysconfig; value=sysconfig.get_config_var('Py_GIL_DISABLED'); print(sys.executable); print(sys.version); print('Py_GIL_DISABLED=', value); raise SystemExit(1 if str(value).strip().lower() not in ('none', '0', 'false', '') else 0)"
}

Invoke-Checked "Upgrade pip" { python -m pip install --upgrade pip }
Invoke-Checked "Install project extras" { python -m pip install -e ".[dev,rembg]" }
Invoke-Checked "Compile sources" { python -m compileall -q src tests }
Invoke-Checked "Run ruff" { python -m ruff check . }
Invoke-Checked "Run tests" { python -m pytest }
Invoke-Checked "Check rembg backend" { python -m resolume_alpha_tool.cli rembg-check }

if ($LaunchApp) {
    Invoke-Checked "Launch GUI" { python -m resolume_alpha_tool.app }
} else {
    Write-Host ""
    Write-Host "Local verification complete. Start GUI with:"
    Write-Host "python -m resolume_alpha_tool.app"
}
