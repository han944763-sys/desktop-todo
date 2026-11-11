from __future__ import annotations

import os
import sys
from pathlib import Path


APP_DIR_NAME = "DesktopTodo"


def app_data_dir() -> Path:
    """Return the per-user writable application directory."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_DIR_NAME
    return Path.home() / ".desktop-todo"


def database_path() -> Path:
    return app_data_dir() / "todo.db"


def asset_path(name: str) -> Path:
    return Path(__file__).resolve().parent / "assets" / name
