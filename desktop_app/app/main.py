from __future__ import annotations

from PySide6.QtCore import QTimer

from .application import build_application
from .update_dialog import check_for_updates


def run() -> None:
    app, window = build_application()
    window.show()
    QTimer.singleShot(1200, lambda: check_for_updates(window))
    app.exec()
