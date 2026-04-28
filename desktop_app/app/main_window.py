from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from desktop_app.app.activation_dialog import ActivationDialog
from desktop_app.config.app_info import APP_NAME
from desktop_app.config.paths import resource_dir
from desktop_app.modules.modules_index.page import ModulesPage
from desktop_app.modules.registry import STATIC_PAGES
from desktop_app.state.models import LicenseStatusSnapshot
from desktop_app.ui.widgets import StatusBadge


class MainWindow(QMainWindow):
    def __init__(self, context) -> None:
        super().__init__()
        self.context = context
        self.context.main_window = self
        self.setWindowTitle(APP_NAME)

        assets_dir = resource_dir()
        logo_path = assets_dir / "logo1.png"
        icon_path = assets_dir / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        elif logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self.resize(1380, 900)
        self.pages: dict[str, QWidget] = {}
        self.current_module_page: QWidget | None = None

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setProperty("sidebar", True)
        sidebar.setFixedWidth(290)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(22, 24, 22, 22)
        sidebar_layout.setSpacing(18)

        brand = QWidget()
        brand.setStyleSheet("background: transparent;")
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(0)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setObjectName("brandLogo")
        logo_label.setStyleSheet("background: transparent;")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path)).scaledToWidth(230, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        brand_layout.addWidget(logo_label)
        sidebar_layout.addWidget(brand)

        self.nav_list = QListWidget()
        self.nav_list.setFocusPolicy(Qt.NoFocus)
        for key, label in [
            ("modules", "Рњодули"),
            ("history", "История операций"),
            ("settings", "Настройки"),
            ("license", "Лицензия"),
            ("about", "О программе"),
        ]:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, key)
            self.nav_list.addItem(item)
        self.nav_list.currentItemChanged.connect(self._handle_nav_changed)
        sidebar_layout.addWidget(self.nav_list, 1)
        root_layout.addWidget(sidebar)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(34, 28, 34, 22)
        body_layout.setSpacing(20)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)
        self.page_title = QLabel("Модули")
        self.page_title.setProperty("title", True)
        header_layout.addWidget(self.page_title)
        header_layout.addStretch(1)
        self.header_badge = StatusBadge("Проверка...", "warning")
        header_layout.addWidget(self.header_badge)
        self.activate_button = QPushButton("Активировать")
        self.activate_button.clicked.connect(self.open_activation_dialog)
        header_layout.addWidget(self.activate_button)
        body_layout.addWidget(header)

        self.stack = QStackedWidget()
        body_layout.addWidget(self.stack, 1)
        root_layout.addWidget(body, 1)

        self.setCentralWidget(root)
        self._create_static_pages()
        self.nav_list.setCurrentRow(0)

        snapshot = self.context.license_service.get_snapshot()
        self.update_license_snapshot(snapshot)
        if self._should_open_activation(snapshot):
            QTimer.singleShot(200, self.open_activation_dialog)

    def _create_static_pages(self) -> None:
        modules_page = ModulesPage(self.context)
        modules_page.module_requested.connect(self.open_module)
        self.pages["modules"] = modules_page
        self.stack.addWidget(modules_page)

        for key, page_cls in STATIC_PAGES.items():
            if key == "modules":
                continue
            page = page_cls(self.context)
            self.pages[key] = page
            self.stack.addWidget(page)

    def _handle_nav_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        self.navigate(current.data(Qt.UserRole))

    def navigate(self, key: str) -> None:
        self.page_title.setText(self._title_for_key(key))
        page = self.pages[key]
        self.stack.setCurrentWidget(page)
        if key == "history":
            self.refresh_history_page()
        if key == "license":
            page.refresh()  # type: ignore[attr-defined]

    def open_module(self, module_id: str) -> None:
        try:
            descriptor = self.context.registry.get(module_id)
            if self.current_module_page is not None:
                self.stack.removeWidget(self.current_module_page)
                self.current_module_page.deleteLater()
            page = descriptor.page_factory(self.context)
            page.back_requested.connect(lambda: self.navigate("modules"))  # type: ignore[attr-defined]
            self.current_module_page = page
            self.stack.addWidget(page)
            self.stack.setCurrentWidget(page)
            self.page_title.setText(descriptor.title)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Не удалось открыть модуль",
                f"Модуль '{module_id}' не открылся.\n\nОшибка: {exc}",
            )

    def open_activation_dialog(self) -> None:
        dialog = ActivationDialog(self.context, self)
        if dialog.exec():
            snapshot = self.context.license_service.get_snapshot()
            self.update_license_snapshot(snapshot)
            self.refresh_license_page()

    def update_license_snapshot(self, snapshot: LicenseStatusSnapshot) -> None:
        self.header_badge.setText(snapshot.status_text)
        self.header_badge.set_kind("success" if snapshot.is_active else ("danger" if snapshot.error else "warning"))

    def refresh_history_page(self) -> None:
        page = self.pages.get("history")
        if page is not None:
            page.refresh()  # type: ignore[attr-defined]

    def refresh_license_page(self) -> None:
        page = self.pages.get("license")
        if page is not None:
            page.refresh()  # type: ignore[attr-defined]

    @staticmethod
    def _should_open_activation(snapshot: LicenseStatusSnapshot) -> bool:
        if snapshot.is_active:
            return False
        if not snapshot.license_key:
            return True
        lowered = (snapshot.error or snapshot.status_text).casefold()
        return "api недоступен" not in lowered

    @staticmethod
    def _title_for_key(key: str) -> str:
        mapping = {
            "modules": "Модули",
            "history": "История операций",
            "settings": "Настройки",
            "license": "Лицензия",
            "about": "О программе",
        }
        return mapping.get(key, APP_NAME)
