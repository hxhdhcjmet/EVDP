"""Shared filesystem paths for EVDP."""

from pathlib import Path
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"
UPLOAD_DIR = Path(tempfile.gettempdir()) / "evdp_uploads"


def ensure_runtime_dirs() -> None:
    """Create directories used by the UI and crawlers at runtime."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def project_path(*parts: str) -> Path:
    return PROJECT_ROOT.joinpath(*parts)
