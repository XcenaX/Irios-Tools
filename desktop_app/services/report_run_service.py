from __future__ import annotations

from pathlib import Path

from desktop_app.config.paths import legacy_base_dir
from desktop_app.state.models import RunHistoryRecord, RunRequest, RunResult, now_iso
from shared.missing_originals import build_company_output_path, resolve_report_company_name

from .history_service import HistoryService
from .license_service import humanize_error_message
from .missing_originals_service import MissingOriginalsService
from .settings_service import SettingsService


class ReportRunService:
    def __init__(
        self,
        *,
        report_service: MissingOriginalsService,
        history_service: HistoryService,
        settings_service: SettingsService,
    ) -> None:
        self.report_service = report_service
        self.history_service = history_service
        self.settings_service = settings_service
        self.base_dir = legacy_base_dir()

    def default_output_path(self, receipts_file: Path, sales_file: Path) -> Path:
        company_name = resolve_report_company_name(receipts_file, sales_file)
        settings = self.settings_service.load()
        base_dir = Path(settings.output_dir) if settings.output_dir else self.base_dir
        return build_company_output_path(base_dir, company_name)

    def run_missing_originals(
        self,
        receipts_file: Path,
        sales_file: Path,
        output_file: Path | None = None,
    ) -> RunResult:
        target = output_file or self.default_output_path(receipts_file, sales_file)
        request = RunRequest(
            module_id="missing_originals",
            receipts_file=receipts_file,
            sales_file=sales_file,
            output_file=target,
        )
        try:
            result = self.report_service.build_report(request)
            self._append_history(
                RunHistoryRecord(
                    module_id=request.module_id,
                    started_at=now_iso(),
                    status="success",
                    receipts_file=str(receipts_file),
                    sales_file=str(sales_file),
                    output_file=str(result.output_file),
                    message=f"Сформировано строк: {result.total_count}",
                    company_name=result.company_name,
                )
            )
            return result
        except Exception as exc:
            message = humanize_error_message(str(exc))
            self._append_history(
                RunHistoryRecord(
                    module_id=request.module_id,
                    started_at=now_iso(),
                    status="error",
                    receipts_file=str(receipts_file),
                    sales_file=str(sales_file),
                    output_file=str(target),
                    message=message,
                )
            )
            raise type(exc)(message) from exc

    def _append_history(self, record: RunHistoryRecord) -> None:
        limit = self.settings_service.load().history_limit
        self.history_service.append(record, limit=limit)
