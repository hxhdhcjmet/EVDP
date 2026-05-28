#!/bin/bash
# EVDP uv environment setup script for Linux / macOS / WSL.
# Usage: bash uv_setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_uv() {
    if ! command -v uv &> /dev/null; then
        log_error "uv is not installed."
        echo "  Install guide: https://docs.astral.sh/uv/getting-started/installation/"
        echo "  macOS/Linux:  curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    log_info "Detected $(uv --version)"
}

main() {
    echo ""
    echo "  EVDP uv setup"
    echo ""

    cd "$SCRIPT_DIR"
    check_uv

    log_info "Creating/updating .venv and installing default dependencies..."
    uv sync

    log_info "Installing Playwright Chromium..."
    uv run python -m playwright install chromium

    log_warn "AI and database dependencies are optional."
    echo "  Install AI support:       uv sync --extra ai"
    echo "  Install database support: uv sync --extra db"
    echo "  Install all extras:       uv sync --extra all"
    echo ""
    echo "  Start EVDP with: bash uv_run.sh"
    echo ""
}

main "$@"
