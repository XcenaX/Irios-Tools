from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFormLayout, QPushButton, QVBoxLayout, QWidget

from desktop_app.ui.widgets import AlertBanner, AppCard, SectionHeader


class SettingsPage(QWidget):
    def __init__(self, context) -> None:
        super().__init__()
        self.context = context
        self.alert = AlertBanner()
        settings = self.context.settings_service.load()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(SectionHeader("", "Пока оставили только базовый выбор темы интерфейса."))
        layout.addWidget(self.alert)

        card = AppCard()
        form = QFormLayout()
        form.setContentsMargins(8, 8, 8, 8)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(16)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.theme_combo = QComboBox()
        self.theme_combo.setMinimumWidth(280)
        self.theme_combo.setMaximumWidth(360)
        self.theme_combo.addItem("Как в системе", "system")
        self.theme_combo.addItem("Светлая", "light")
        self.theme_combo.addItem("Темная", "dark")
        current_index = max(0, self.theme_combo.findData(settings.theme_mode))
        self.theme_combo.setCurrentIndex(current_index)
        form.addRow("Тема", self.theme_combo)
        card.layout.addLayout(form)

        save_button = QPushButton("Сохранить")
        save_button.setProperty("primary", True)
        save_button.clicked.connect(self.save_settings)
        card.layout.addWidget(save_button, alignment=Qt.AlignLeft)

        layout.addWidget(card)
        layout.addStretch(1)

    def save_settings(self) -> None:
        settings = self.context.settings_service.load()
        settings.theme_mode = str(self.theme_combo.currentData())
        self.context.settings_service.save(settings)
        self.alert.set_message("Тема сохранена.", "success")
