from __future__ import annotations

import json
import os
import sys
from pathlib import Path

APP_NAME = "Physics AI Manager"


def app_root() -> Path:
    """Return the source/frozen application root."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[1]


def icon_path() -> Path:
    return app_root() / "assets" / "icon.png"


def config_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
        return base / "PhysicsAIManager"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "PhysicsAIManager"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "physics-ai-manager"


def config_path() -> Path:
    return config_dir() / "config.json"


def load_config() -> dict:
    path = config_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(data: dict) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def find_library_root(config: dict | None = None) -> Path:
    """Find the blueprint library, allowing an editable external override."""
    env = os.environ.get("PHYSAI_LIBRARY")
    if env:
        p = Path(env).expanduser().resolve()
        if (p / "MASTER_MANIFEST.json").is_file():
            return p

    config = config or load_config()
    override = config.get("library_path")
    if override:
        p = Path(override).expanduser().resolve()
        if (p / "MASTER_MANIFEST.json").is_file():
            return p

    # An editable library beside the executable/source takes precedence.
    if getattr(sys, "frozen", False):
        sibling = Path(sys.executable).resolve().parent / "library"
    else:
        sibling = app_root() / "library"
    if (sibling / "MASTER_MANIFEST.json").is_file():
        return sibling

    bundled = app_root() / "library"
    if (bundled / "MASTER_MANIFEST.json").is_file():
        return bundled

    raise FileNotFoundError(
        "Could not find the Physics AI blueprint library. Set PHYSAI_LIBRARY or "
        "place a library folder beside the application."
    )
