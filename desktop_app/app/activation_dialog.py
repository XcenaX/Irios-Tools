from __future__ import annotations

from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from desktop_app.ui.widgets import AlertBanner


class ActivationDialog(QDialog):
    def __init__(self, context, parent=None, *, license_service=None, title_text: str | None = None) -> None:
        super().__init__(parent)
        self.context = context
        self.license_service = license_service or self.context.license_service
        self.setWindowTitle(title_text or "Активация лицензии")
        self.setModal(True)
        self.resize(480, 240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel(title_text or "Введите ключ активации")
        title.setProperty("sectionTitle", True)
        layout.addWidget(title)

        description = QLabel(
            "После активации приложение проверит подписку и сохранит токен на этом устройстве."
        )
        description.setWordWrap(True)
        description.setProperty("muted", True)
        layout.addWidget(description)

        self.alert = AlertBanner()
        layout.addWidget(self.alert)

        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("Например, IRIOS-DEMO-KEY")
        self.key_edit.setText(self.license_service.load_config().license_key)
        layout.addWidget(self.key_edit)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        activate_button = QPushButton("Активировать")
        activate_button.setProperty("primary", True)
        activate_button.clicked.connect(self.activate)
        button_row.addWidget(cancel_button)
        button_row.addWidget(activate_button)
        button_row.addStretch(1)
        layout.addLayout(button_row)

    def activate(self) -> None:
        if len(self.key_edit.text().strip()) < 4:
            self.alert.set_message("Введите корректный ключ лицензии.", "error")
            return
        try:
            self.license_service.activate(self.key_edit.text())
            self.accept()
        except Exception as exc:
            self.alert.set_message(str(exc), "error")
