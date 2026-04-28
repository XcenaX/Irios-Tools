from __future__ import annotations

from dataclasses import dataclass

from desktop_app.services.history_service import HistoryService
from desktop_app.services.hr_documents_service import HRDocumentsService
from desktop_app.services.license_service import LicenseService
from desktop_app.services.materials_writeoff_service import MaterialsWriteoffService
from desktop_app.services.missing_originals_service import MissingOriginalsService
from desktop_app.services.report_run_service import ReportRunService
from desktop_app.services.settings_service import SettingsService


@dataclass
class AppContext:
    settings_service: SettingsService
    history_service: HistoryService
    license_service: LicenseService
    missing_originals_service: MissingOriginalsService
    hr_documents_service: HRDocumentsService
    materials_writeoff_service: MaterialsWriteoffService
    report_run_service: ReportRunService
    registry: object | None = None
    main_window: object | None = None


def build_context(*, include_ui: bool = True) -> AppContext:
    settings_service = SettingsService()
    history_service = HistoryService()
    settings = settings_service.load()
    license_service = LicenseService(api_base_url=settings.api_base_url or None)
    missing_originals_service = MissingOriginalsService(license_service)
    hr_documents_service = HRDocumentsService(
        license_service=license_service,
        history_service=history_service,
        settings_service=settings_service,
    )
    materials_writeoff_service = MaterialsWriteoffService(
        settings_service=settings_service,
        history_service=history_service,
        license_service=license_service,
        api_base_url=settings.api_base_url or None,
    )
    report_run_service = ReportRunService(
        report_service=missing_originals_service,
        history_service=history_service,
        settings_service=settings_service,
    )
    registry = None
    if include_ui:
        from desktop_app.modules.registry import ModuleRegistry

        registry = ModuleRegistry()

    return AppContext(
        settings_service=settings_service,
        history_service=history_service,
        license_service=license_service,
        missing_originals_service=missing_originals_service,
        hr_documents_service=hr_documents_service,
        materials_writeoff_service=materials_writeoff_service,
        report_run_service=report_run_service,
        registry=registry,
    )
