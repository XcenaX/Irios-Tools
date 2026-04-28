from __future__ import annotations

from functools import partial

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from desktop_app.ui.widgets import AppCard, SectionHeader, StatusBadge


class ModulesPage(QWidget):
    module_requested = Signal(str)

    def __init__(self, context) -> None:
        super().__init__()
        self.context = context
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(SectionHeader("", "Единая точка входа во все рабочие инструменты платформы."))

        container = QWidget()
        cards_layout = QVBoxLayout(container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(14)

        for descriptor in self.context.registry.modules():
            card = AppCard()
            badge = StatusBadge(descriptor.category, "info")
            badge.setProperty("badgeKind", "warning")
            badge.set_kind("warning")
            title = QLabel(descriptor.title)
            title.setProperty("sectionTitle", True)
            summary = QLabel(descriptor.summary)
            summary.setWordWrap(True)
            summary.setProperty("muted", True)
            open_button = QPushButton("Открыть модуль")
            open_button.setProperty("primary", True)
            open_button.clicked.connect(partial(self._request_module, descriptor.id))
            card.layout.addWidget(badge, alignment=Qt.AlignLeft)
            card.layout.addWidget(title)
            card.layout.addWidget(summary)
            card.layout.addWidget(open_button, alignment=Qt.AlignLeft)
            cards_layout.addWidget(card)

        cards_layout.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

    def _request_module(self, module_id: str, *_args) -> None:
        self.module_requested.emit(module_id)
