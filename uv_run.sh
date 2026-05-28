#!/bin/bash
# EVDP uv launch script for Linux / macOS / WSL.
# Usage: bash uv_run.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PORT:-8501}"

cd "$SCRIPT_DIR"

if ! command -v uv &> /dev/null; then
    echo "[ERROR] uv is not installed. Run setup.sh or install uv first."
    exit 1
fi

echo "[INFO] Starting EVDP at http://localhost:${PORT}"
uv run streamlit run app.py --server.port "$PORT"
