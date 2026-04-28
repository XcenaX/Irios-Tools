from __future__ import annotations

from PySide6.QtWidgets import QApplication

from desktop_app.config.app_info import APP_NAME, APP_ORGANIZATION
from desktop_app.config.theme import LIGHT_THEME

from .context import build_context
from .main_window import MainWindow


def build_application() -> tuple[QApplication, MainWindow]:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORGANIZATION)
    app.setStyleSheet(LIGHT_THEME)
    context = build_context()
    window = MainWindow(context)
    return app, window
