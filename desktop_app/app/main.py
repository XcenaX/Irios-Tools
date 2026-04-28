from __future__ import annotations

from .application import build_application


def run() -> None:
    app, window = build_application()
    window.show()
    app.exec()
