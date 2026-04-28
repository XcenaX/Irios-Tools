from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QFrame, QLabel, QPushButton, QVBoxLayout, QWidget


class AppCard(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("card", True)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(12)


class StatusBadge(QLabel):
    def __init__(self, text: str, kind: str = "success", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setProperty("badge", True)
        self.set_kind(kind)

    def set_kind(self, kind: str) -> None:
        self.setProperty("badgeKind", kind)
        self.style().unpolish(self)
        self.style().polish(self)


class AlertBanner(QLabel):
    def __init__(self, text: str = "", kind: str = "info", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setProperty("alert", True)
        self.set_kind(kind)
        self.setVisible(bool(text))

    def set_message(self, text: str, kind: str) -> None:
        self.setText(text)
        self.set_kind(kind)
        self.setVisible(bool(text))

    def set_kind(self, kind: str) -> None:
        self.setProperty("alertKind", kind)
        self.style().unpolish(self)
        self.style().polish(self)


class FileDropField(AppCard):
    file_changed = Signal(str)

    def __init__(
        self,
        title: str,
        button_text: str,
        parent: QWidget | None = None,
        file_filter: str = "Excel files (*.xls *.xlsx);;All files (*.*)",
    ) -> None:
        super().__init__(parent)
        self.file_filter = file_filter
        self.title = QLabel(title)
        self.title.setProperty("sectionTitle", True)
        self.path_label = QLabel("Файл не выбран")
        self.path_label.setWordWrap(True)
        self.path_label.setProperty("muted", True)
        self.button = QPushButton(button_text)
        self.button.clicked.connect(self._choose_file)
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.path_label)
        self.layout.addWidget(self.button, alignment=Qt.AlignLeft)
        self.setAcceptDrops(True)

    def path(self) -> str:
        return self.path_label.text() if self.path_label.text() != "Файл не выбран" else ""

    def set_path(self, path: str) -> None:
        self.path_label.setText(path or "Файл не выбран")
        self.file_changed.emit(path)

    def _choose_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.title.text(),
            "",
            self.file_filter,
        )
        if file_path:
            self.set_path(file_path)

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        urls = event.mimeData().urls()
        if not urls:
            return
        self.set_path(urls[0].toLocalFile())
        event.acceptProposedAction()


class SectionHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        if title:
            title_label = QLabel(title)
            title_label.setProperty("title", True)
            layout.addWidget(title_label)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setProperty("muted", True)
            subtitle_label.setWordWrap(True)
            layout.addWidget(subtitle_label)
