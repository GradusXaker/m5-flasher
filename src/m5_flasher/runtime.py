from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSettings


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def portable_marker_path() -> Path:
    return app_root() / "portable.ini"


def is_portable_mode() -> bool:
    return portable_marker_path().exists()


def create_settings(org: str, app: str) -> QSettings:
    if is_portable_mode():
        return QSettings(str(app_root() / f"{app}.ini"), QSettings.Format.IniFormat)
    return QSettings(org, app)
