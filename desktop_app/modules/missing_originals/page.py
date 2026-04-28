from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QProgressBar, QVBoxLayout, QWidget

from desktop_app.state.models import RunResult
from desktop_app.ui.widgets import AlertBanner, AppCard, FileDropField, SectionHeader


class WorkerSignals(QObject):
    success = Signal(object)
    error = Signal(str)


class BuildWorker(QRunnable):
    def __init__(self, context, receipts_path: str, sales_path: str) -> None:
        super().__init__()
        self.context = context
        self.receipts_path = Path(receipts_path)
        self.sales_path = Path(sales_path)
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            result = self.context.report_run_service.run_missing_originals(self.receipts_path, self.sales_path)
            self.signals.success.emit(result)
        except Exception as exc:
            self.signals.error.emit(str(exc))


class MissingOriginalsModulePage(QWidget):
    back_requested = Signal()

    def __init__(self, context) -> None:
        super().__init__()
        self.context = context
        self.thread_pool = QThreadPool.globalInstance()
        self.last_result: RunResult | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        top_row = QHBoxLayout()
        back_button = QPushButton("Назад к модулям")
        back_button.clicked.connect(self.back_requested.emit)
        top_row.addWidget(back_button, alignment=Qt.AlignLeft)
        top_row.addStretch(1)
        layout.addLayout(top_row)

        layout.addWidget(
            SectionHeader(
                "",
                "Сборка отчёта по двум Excel-файлам с использованием существующей бизнес-логики.",
            )
        )

        self.alert = AlertBanner()
        layout.addWidget(self.alert)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self.receipts_field = FileDropField("Поступления", "Выбрать файл поступлений")
        self.sales_field = FileDropField("Реализация", "Выбрать файл реализации")
        cards_row.addWidget(self.receipts_field, 1)
        cards_row.addWidget(self.sales_field, 1)

        actions_card = AppCard()
        actions_card.layout.setSpacing(10)
        title = QLabel("Действия")
        title.setProperty("sectionTitle", True)
        self.run_button = QPushButton("Сформировать отчёт")
        self.run_button.setProperty("primary", True)
        self.run_button.clicked.connect(self.start_run)
        self.open_folder_button = QPushButton("Открыть папку результата")
        self.open_folder_button.setVisible(False)
        self.open_folder_button.clicked.connect(self.open_output_folder)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.status_label = QLabel("Выберите два исходных файла.")
        self.status_label.setProperty("muted", True)
        self.status_label.setWordWrap(True)
        actions_card.layout.addWidget(title)
        actions_card.layout.addWidget(self.run_button, alignment=Qt.AlignLeft)
        actions_card.layout.addWidget(self.open_folder_button, alignment=Qt.AlignLeft)
        actions_card.layout.addWidget(self.progress)
        actions_card.layout.addWidget(self.status_label)
        actions_card.layout.addStretch(1)
        cards_row.addWidget(actions_card, 1)

        layout.addLayout(cards_row)
        layout.addStretch(1)

    def start_run(self) -> None:
        snapshot = self.context.license_service.get_snapshot()
        if not snapshot.is_active:
            self.alert.set_message(snapshot.error or "Подписка неактивна. Перейдите на вкладку лицензии.", "error")
            self.context.main_window.navigate("license")
            return

        receipts = self.receipts_field.path().strip()
        sales = self.sales_field.path().strip()
        if not receipts or not Path(receipts).is_file():
            self.alert.set_message("Выберите корректный файл поступлений.", "error")
            return
        if not sales or not Path(sales).is_file():
            self.alert.set_message("Выберите корректный файл реализации.", "error")
            return

        self.alert.setVisible(False)
        self.progress.setVisible(True)
        self.run_button.setEnabled(False)
        self.open_folder_button.setVisible(False)
        self.status_label.setText("Формирую отчёт...")
        worker = BuildWorker(self.context, receipts, sales)
        worker.signals.success.connect(self._on_success)
        worker.signals.error.connect(self._on_error)
        self.thread_pool.start(worker)

    def _on_success(self, result: RunResult) -> None:
        self.last_result = result
        self.progress.setVisible(False)
        self.run_button.setEnabled(True)
        self.open_folder_button.setVisible(True)
        self.status_label.setText(
            f"Готово: {result.company_name}\n"
            f"{result.output_file.name}"
        )
        self.alert.set_message("Отчёт успешно сформирован и сохранён.", "success")
        self.context.main_window.refresh_history_page()

    def _on_error(self, error_text: str) -> None:
        self.progress.setVisible(False)
        self.run_button.setEnabled(True)
        self.open_folder_button.setVisible(False)
        self.status_label.setText("Операция завершилась ошибкой.")
        self.alert.set_message(error_text, "error")
        self.context.main_window.refresh_history_page()

    def open_output_folder(self) -> None:
        if self.last_result:
            os.startfile(str(self.last_result.output_file.parent))
