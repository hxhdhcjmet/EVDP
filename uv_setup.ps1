# EVDP uv environment setup script for Windows PowerShell.
# Usage: .\uv_setup.ps1

$ErrorActionPreference = "Stop"

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERROR] $msg" -ForegroundColor Red }

try {
    $uvVersion = uv --version
    Write-Info "Detected $uvVersion"
} catch {
    Write-Err "uv is not installed."
    Write-Host "  Install guide: https://docs.astral.sh/uv/getting-started/installation/"
    Write-Host "  Windows PowerShell: powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
    exit 1
}

Set-Location $PSScriptRoot

Write-Info "Creating/updating .venv and installing default dependencies..."
uv sync

Write-Info "Installing Playwright Chromium..."
uv run python -m playwright install chromium

Write-Warn "AI and database dependencies are optional."
Write-Host "  Install AI support:       uv sync --extra ai"
Write-Host "  Install database support: uv sync --extra db"
Write-Host "  Install all extras:       uv sync --extra all"
Write-Host ""
Write-Host "  Start EVDP with: .\uv_run.ps1"
Write-Host ""
