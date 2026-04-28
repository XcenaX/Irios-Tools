from __future__ import annotations

from desktop_app.modules.about.page import AboutPage
from desktop_app.modules.history.page import HistoryPage
from desktop_app.modules.hr_documents.page import HRDocumentsModulePage
from desktop_app.modules.license.page import LicensePage
from desktop_app.modules.materials_writeoff.page import MaterialsWriteoffModulePage
from desktop_app.modules.missing_originals.page import MissingOriginalsModulePage
from desktop_app.modules.modules_index.page import ModulesPage
from desktop_app.modules.settings.page import SettingsPage

from .base import ModuleDescriptor


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: list[ModuleDescriptor] = [
            ModuleDescriptor(
                id="missing_originals",
                title="Недостающие оригиналы документов",
                summary="Формирование отчёта по недостающим оригиналам документов из Excel-файлов.",
                category="Отчёты",
                order=10,
                page_factory=lambda context: MissingOriginalsModulePage(context),
                is_enabled=lambda _context: True,
            ),
            ModuleDescriptor(
                id="hr_documents",
                title="Кадровые документы",
                summary="Формирование трудового договора и приказа о приеме из карточки Т-2.",
                category="HR",
                order=20,
                page_factory=lambda context: HRDocumentsModulePage(context),
                is_enabled=lambda _context: True,
            ),
            ModuleDescriptor(
                id="materials_writeoff",
                title="Списание материалов",
                summary="Формирование итоговой Excel-книги по акту / smart contract и ведомости остатков.",
                category="Склад",
                order=30,
                page_factory=lambda context: MaterialsWriteoffModulePage(context),
                is_enabled=lambda _context: True,
            ),
        ]

    def modules(self) -> list[ModuleDescriptor]:
        return sorted(self._modules, key=lambda item: item.order)

    def get(self, module_id: str) -> ModuleDescriptor:
        for module in self._modules:
            if module.id == module_id:
                return module
        raise KeyError(module_id)


STATIC_PAGES = {
    "modules": ModulesPage,
    "history": HistoryPage,
    "settings": SettingsPage,
    "license": LicensePage,
    "about": AboutPage,
}
