from __future__ import annotations

import os
import sys
from pathlib import Path


def resource_dir() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def project_root() -> Path:
    return app_dir()


def legacy_base_dir() -> Path:
    return app_dir()


def user_data_dir() -> Path:
    app_name = "IriosTools"
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path.home() / ".config"
    path = base / app_name
    path.mkdir(parents=True, exist_ok=True)
    return path


def history_file_path() -> Path:
    return user_data_dir() / "history.json"


def settings_file_path() -> Path:
    return user_data_dir() / "settings.json"
