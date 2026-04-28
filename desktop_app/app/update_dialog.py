from __future__ import annotations

import threading

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QMessageBox, QProgressBar, QVBoxLayout, QWidget

from desktop_app.services.update_service import UpdateInfo, UpdateService


def check_for_updates(parent: QWidget) -> None:
    service = UpdateService()
    if not service.should_check_updates():
        return

    state: dict[str, object] = {"done": False, "update": None, "error": None}

    def worker() -> None:
        try:
            state["update"] = service.fetch_update_info()
        except Exception as exc:
            state["error"] = exc
        finally:
            state["done"] = True

    threading.Thread(target=worker, daemon=True).start()
    timer = QTimer(parent)
    parent._update_check_timer = timer  # type: ignore[attr-defined]

    def poll() -> None:
        if not state["done"]:
            return
        timer.stop()
        update = state.get("update")
        if isinstance(update, UpdateInfo):
            dialog = UpdateDialog(update, service, parent)
            dialog.exec()

    timer.timeout.connect(poll)
    timer.start(250)


class UpdateDialog(QDialog):
    def __init__(self, update: UpdateInfo, service: UpdateService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.update = update
        self.service = service
        self._lock = threading.Lock()
        self._downloaded = 0
        self._total = update.size
        self._done = False
        self._error: Exception | None = None
        self._script_path = None

        self.setWindowTitle("Обновление")
        self.setModal(True)
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        self.message_label = QLabel(update.message or "Подождите, программа обновляется")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel(f"Скачивание версии {update.version}...")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_worker)
        self._timer.start(150)

        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self) -> None:
        try:
            downloaded_exe = self.service.download_update(self.update, progress=self._set_progress)
            script_path = self.service.create_updater_script(downloaded_exe)
            with self._lock:
                self._script_path = script_path
        except Exception as exc:
            with self._lock:
                self._error = exc
        finally:
            with self._lock:
                self._done = True

    def _set_progress(self, downloaded: int, total: int) -> None:
        with self._lock:
            self._downloaded = downloaded
            self._total = total

    def _poll_worker(self) -> None:
        with self._lock:
            downloaded = self._downloaded
            total = self._total
            done = self._done
            error = self._error
            script_path = self._script_path

        if total:
            self.progress_bar.setValue(min(100, int(downloaded * 100 / total)))
        else:
            self.progress_bar.setRange(0, 0)

        if not done:
            return

        self._timer.stop()
        if error is not None:
            QMessageBox.critical(self, "Ошибка обновления", str(error))
            self.reject()
            return

        if script_path is not None:
            self.status_label.setText("Перезапуск новой версии...")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.service.launch_updater(script_path)
            QApplication.quit()
