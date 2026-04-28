from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from desktop_app.ui.widgets import AlertBanner, AppCard, SectionHeader, StatusBadge


class LicensePage(QWidget):
    def __init__(self, context) -> None:
        super().__init__()
        self.context = context
        self.alert = AlertBanner()
        self.badge = StatusBadge("Проверка...", "warning")
        self.status_value = QLabel("-")
        self.expires_value = QLabel("-")
        self.key_value = QLabel("-")
        self.device_value = QLabel("-")
        self.checked_value = QLabel("-")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(SectionHeader("", "Подписка продлевается администратором после оплаты."))
        layout.addWidget(self.alert)

        card = AppCard()
        card.layout.addWidget(self.badge, alignment=Qt.AlignLeft)

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(14)
        grid.addWidget(QLabel("Статус"), 0, 0)
        grid.addWidget(self.status_value, 0, 1)
        grid.addWidget(QLabel("Действует до"), 1, 0)
        grid.addWidget(self.expires_value, 1, 1)
        grid.addWidget(QLabel("Ключ"), 2, 0)
        grid.addWidget(self.key_value, 2, 1)
        grid.addWidget(QLabel("Устройство"), 3, 0)
        grid.addWidget(self.device_value, 3, 1)
        grid.addWidget(QLabel("Последняя проверка"), 4, 0)
        grid.addWidget(self.checked_value, 4, 1)
        card.layout.addLayout(grid)

        note = QLabel(
            "Если статус неактивен, нажмите кнопку активации в шапке приложения. "
            "Продление выполняется со стороны администратора."
        )
        note.setWordWrap(True)
        note.setProperty("muted", True)
        card.layout.addWidget(note)

        layout.addWidget(card)
        layout.addStretch(1)
        self.refresh()

    def refresh(self) -> None:
        snapshot = self.context.license_service.get_snapshot()
        self.status_value.setText(snapshot.status_text)
        self.expires_value.setText(snapshot.expires_at or "Не указано")
        self.key_value.setText(snapshot.license_key or "Не указан")
        self.device_value.setText(f"{snapshot.device_name} / {snapshot.device_id}")
        self.device_value.setWordWrap(True)
        self.checked_value.setText(snapshot.last_checked_at or "Ещё не проверялась")
        badge_kind = "success" if snapshot.is_active else ("danger" if snapshot.error else "warning")
        self.badge.setText(snapshot.status_text)
        self.badge.set_kind(badge_kind)
        if snapshot.error:
            self.alert.set_message(snapshot.error, "error")
        else:
            self.alert.setVisible(False)
        self.context.main_window.update_license_snapshot(snapshot)
