from __future__ import annotations

from desktop_app.state.models import RunRequest, RunResult, now_iso
from shared.license_client import build_report_via_api
from shared.missing_originals import PRODUCT_VERSION, build_payload_from_files, render_report_data_to_excel

from .license_service import LicenseService


class MissingOriginalsService:
    def __init__(self, license_service: LicenseService) -> None:
        self.license_service = license_service

    def build_report(self, request: RunRequest) -> RunResult:
        self.license_service.ensure_valid_or_raise()
        config = self.license_service.load_config()
        payload = build_payload_from_files(request.receipts_file, request.sales_file)
        response = build_report_via_api(
            api_base_url=config.api_base_url,
            token=config.token,
            device_id=config.device_id,
            payload_version=PRODUCT_VERSION,
            payload=payload,
        )
        build_result = render_report_data_to_excel(response["report_data"], request.output_file)
        return RunResult(
            module_id=request.module_id,
            output_file=build_result.output_file,
            company_name=build_result.company_name,
            receipts_count=build_result.receipts_count,
            sales_count=build_result.sales_count,
            completed_at=now_iso(),
        )
