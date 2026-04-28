from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from typing import Any

from desktop_app.config.paths import legacy_base_dir
from desktop_app.state.models import HRDocumentsRunResult, RunHistoryRecord, now_iso
from shared.hr_documents import build_hr_documents_payload, load_hr_contract_templates, load_hr_organizations
from shared.hr_documents_contract import PRODUCT_CODE, PRODUCT_VERSION
from shared.license_client import build_hr_documents_via_api

from .history_service import HistoryService
from .license_service import LicenseService, humanize_error_message
from .settings_service import SettingsService


HR_TOKEN_FILE_NAME = ".hr_documents_license.json"


class HRDocumentsService:
    def __init__(
        self,
        *,
        license_service: LicenseService,
        history_service: HistoryService,
        settings_service: SettingsService,
    ) -> None:
        self.license_service = license_service
        self.history_service = history_service
        self.settings_service = settings_service
        self.base_dir = legacy_base_dir()

    def available_organizations(self) -> list[dict[str, str]]:
        registry = load_hr_organizations()["organizations"]
        templates = {
            str(item["template_code"]): str(item.get("template_name", item["template_code"]))
            for item in load_hr_contract_templates()["templates"]
        }
        return [
            {
                "organization_code": str(item["organization_code"]),
                "organization_name": str(item["organization_name"]),
                "default_contract_template_code": str(item.get("default_contract_template_code", "")),
                "default_contract_template_name": templates.get(
                    str(item.get("default_contract_template_code", "")),
                    str(item.get("default_contract_template_code", "")),
                ),
            }
            for item in registry
        ]

    def default_organization_code(self) -> str:
        organizations = self.available_organizations()
        for item in organizations:
            if item["organization_code"]:
                return item["organization_code"]
        return ""

    def default_output_dir(self, organization_code: str) -> Path:
        settings = self.settings_service.load()
        base_dir = Path(settings.output_dir) if settings.output_dir else self.base_dir / "hr_documents"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return base_dir / organization_code / timestamp

    def build_documents(
        self,
        *,
        t2_file: Path,
        organization_code: str,
        contract_template_code: str | None = None,
        salary_clause_mode: str | None = None,
        manual_values: dict[str, Any] | None = None,
        document_requests: list[str] | None = None,
    ) -> HRDocumentsRunResult:
        output_dir = self.default_output_dir(organization_code)
        try:
            result = self._build_documents_impl(
                t2_file=t2_file,
                organization_code=organization_code,
                contract_template_code=contract_template_code,
                salary_clause_mode=salary_clause_mode,
                manual_values=manual_values or {},
                document_requests=document_requests or ["employment_contract", "hire_order"],
                output_dir=output_dir,
            )
            self._append_history(
                RunHistoryRecord(
                    module_id=PRODUCT_CODE,
                    started_at=now_iso(),
                    status="success",
                    receipts_file=str(t2_file),
                    output_file=str(result.output_dir),
                    company_name=organization_code,
                    message=f"Сформировано файлов: {len(result.generated_files)}",
                )
            )
            return result
        except Exception as exc:
            message = humanize_error_message(str(exc))
            self._append_history(
                RunHistoryRecord(
                    module_id=PRODUCT_CODE,
                    started_at=now_iso(),
                    status="error",
                    receipts_file=str(t2_file),
                    output_file=str(output_dir),
                    company_name=organization_code,
                    message=message,
                )
            )
            raise type(exc)(message) from exc

    def _build_documents_impl(
        self,
        *,
        t2_file: Path,
        organization_code: str,
        contract_template_code: str | None,
        salary_clause_mode: str | None,
        manual_values: dict[str, Any],
        document_requests: list[str],
        output_dir: Path,
    ) -> HRDocumentsRunResult:
        self.license_service.ensure_valid_or_raise()
        config = self.license_service.load_config()
        payload = build_hr_documents_payload(
            t2_file=t2_file,
            organization_code=organization_code,
            contract_template_code=contract_template_code,
            salary_clause_mode=salary_clause_mode,
            manual_values=manual_values,
            document_requests=document_requests,
        )
        response = build_hr_documents_via_api(
            api_base_url=config.api_base_url,
            token=config.token,
            device_id=config.device_id,
            payload_version=PRODUCT_VERSION,
            payload=payload,
            product_code=PRODUCT_CODE,
        )
        result_data = response["result_data"]
        generated_files = self._save_documents(output_dir, result_data.get("documents", {}))
        validation = result_data.get("validation", {})
        return HRDocumentsRunResult(
            module_id=PRODUCT_CODE,
            output_dir=output_dir,
            organization_code=organization_code,
            generated_files=generated_files,
            validation_errors=list(validation.get("errors", [])),
            validation_warnings=list(validation.get("warnings", [])),
            completed_at=now_iso(),
        )

    @staticmethod
    def _save_documents(output_dir: Path, documents: dict[str, Any]) -> list[Path]:
        generated_files: list[Path] = []
        output_dir.mkdir(parents=True, exist_ok=True)
        for item in documents.values():
            if not item.get("generated"):
                continue
            filename = str(item["filename"])
            content = base64.b64decode(item["content_base64"])
            target = output_dir / filename
            target.write_bytes(content)
            generated_files.append(target)
        return generated_files

    def _append_history(self, record: RunHistoryRecord) -> None:
        limit = self.settings_service.load().history_limit
        self.history_service.append(record, limit=limit)
