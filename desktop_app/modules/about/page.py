from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from desktop_app.config.app_info import APP_NAME, APP_VERSION
from desktop_app.ui.widgets import AppCard, SectionHeader


class AboutPage(QWidget):
    def __init__(self, _context) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(SectionHeader("", "Платформа для внутренних инструментов и отчётов компании."))
        card = AppCard()
        title = QLabel(APP_NAME)
        title.setProperty("sectionTitle", True)
        card.layout.addWidget(title)
        card.layout.addWidget(QLabel(f"Версия: {APP_VERSION}"))
        description = QLabel(
            "Приложение объединяет модульные инструменты, использует общий shell и переиспользует существующую бизнес-логику отчётов."
        )
        description.setWordWrap(True)
        description.setProperty("muted", True)
        card.layout.addWidget(description)
        layout.addWidget(card)
        layout.addStretch(1)
