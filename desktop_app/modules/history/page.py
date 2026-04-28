from __future__ import annotations

from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from desktop_app.ui.widgets import AppCard, SectionHeader


MODULE_LABELS = {
    "missing_originals": "Недостающие оригиналы",
    "hr_documents": "Кадровые документы",
}


class HistoryPage(QWidget):
    def __init__(self, context) -> None:
        super().__init__()
        self.context = context
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(SectionHeader("", "Последние локально сохранённые запуски модулей."))

        card = AppCard()
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Модуль", "Время", "Статус", "Компания", "Сообщение"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        card.layout.addWidget(self.table)
        layout.addWidget(card, 1)
        self.refresh()

    def refresh(self) -> None:
        records = self.context.history_service.load()
        self.table.setRowCount(len(records))
        for row_index, record in enumerate(records):
            values = [
                MODULE_LABELS.get(record.module_id, record.module_id),
                record.started_at,
                "Успешно" if record.status == "success" else "Ошибка",
                record.company_name or "—",
                record.message or "—",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.table.setItem(row_index, column, item)
