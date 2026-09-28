from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB = BASE_DIR / "data" / "runtime_demo.db"
DEFAULT_TRAY_DB = BASE_DIR / "data" / "runtime_demo_tray.db"
DEFAULT_IMAGES = BASE_DIR / "images"

__all__ = ["BASE_DIR", "DEFAULT_DB", "DEFAULT_TRAY_DB", "DEFAULT_IMAGES"]
