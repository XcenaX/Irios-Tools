from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
from typing import Literal

import requests

from desktop_app.config.paths import legacy_base_dir
from desktop_app.state.models import MaterialsWriteoffRunResult, RunHistoryRecord, now_iso
from shared.license_client import API_REQUEST_HEADERS
from shared.missing_originals import DEFAULT_API_BASE_URL

from .history_service import HistoryService
from .license_service import humanize_error_message
from .settings_service import SettingsService


Mode = Literal["standard", "smart_contract"]


class MaterialsWriteoffService:
    def __init__(
        self,
        *,
        settings_service: SettingsService,
        history_service: HistoryService,
        license_service: object | None = None,
        api_base_url: str | None = None,
    ) -> None:
        self.settings_service = settings_service
        self.history_service = history_service
        self.license_service = license_service
        self.api_base_url = (api_base_url or DEFAULT_API_BASE_URL).rstrip("/")
        self.base_dir = legacy_base_dir()

    def default_output_file(self, mode: Mode) -> Path:
        settings = self.settings_service.load()
        base_dir = Path(settings.output_dir) if settings.output_dir else self.base_dir / "materials_writeoff"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = (
            f"materials_writeoff_result_{timestamp}.xlsx"
            if mode == "standard"
            else f"smart_contract_writeoff_result_{timestamp}.xlsx"
        )
        return base_dir / filename

    def process_files(
        self,
        *,
        ledger_file: Path,
        act_file: Path | None = None,
        appendix_files: list[Path] | None = None,
        mode: Mode = "standard",
        output_file: Path | None = None,
    ) -> MaterialsWriteoffRunResult:
        self._ensure_license()
        target = output_file or self.default_output_file(mode)
        try:
            content = self._request_workbook(
                ledger_file=ledger_file,
                act_file=act_file,
                appendix_files=appendix_files or [],
                mode=mode,
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            result = MaterialsWriteoffRunResult(
                module_id="materials_writeoff",
                output_file=target,
                mode=mode,
                completed_at=now_iso(),
            )
            self._append_history(
                RunHistoryRecord(
                    module_id="materials_writeoff",
                    started_at=now_iso(),
                    status="success",
                    receipts_file=str(act_file or ""),
                    sales_file=str(ledger_file),
                    output_file=str(target),
                    message=(
                        "Сформирована книга списания материалов"
                        if mode == "standard"
                        else "Сформирована книга списания материалов по smart contract"
                    ),
                    company_name="materials_writeoff",
                )
            )
            return result
        except Exception as exc:
            message = humanize_error_message(str(exc))
            self._append_history(
                RunHistoryRecord(
                    module_id="materials_writeoff",
                    started_at=now_iso(),
                    status="error",
                    receipts_file=str(act_file or ""),
                    sales_file=str(ledger_file),
                    output_file=str(target),
                    message=message,
                    company_name="materials_writeoff",
                )
            )
            raise type(exc)(message) from exc

    def match_files(
        self,
        *,
        act_file: Path,
        ledger_file: Path,
        enable_ai: bool = True,
    ) -> dict:
        self._ensure_license()
        with act_file.open("rb") as act_stream, ledger_file.open("rb") as ledger_stream:
            response = requests.post(
                f"{self.api_base_url}/v1/materials-writeoff/match-files",
                headers=API_REQUEST_HEADERS,
                files={
                    "act_file": (act_file.name, act_stream, "application/octet-stream"),
                    "ledger_file": (ledger_file.name, ledger_stream, "application/octet-stream"),
                },
                data={"enable_ai": str(enable_ai).lower()},
                timeout=180,
            )
        self._raise_for_error(response)
        return response.json()

    def extract_act_pdf(self, act_file: Path) -> dict:
        self._ensure_license()
        with act_file.open("rb") as act_stream:
            response = requests.post(
                f"{self.api_base_url}/v1/materials-writeoff/extract-act-pdf",
                headers=API_REQUEST_HEADERS,
                files={"act_file": (act_file.name, act_stream, "application/pdf")},
                timeout=180,
            )
        self._raise_for_error(response)
        return response.json()

    def extract_smart_appendix(self, appendix_file: Path) -> dict:
        self._ensure_license()
        with appendix_file.open("rb") as appendix_stream:
            response = requests.post(
                f"{self.api_base_url}/v1/materials-writeoff/extract-smart-appendix",
                headers=API_REQUEST_HEADERS,
                files={"appendix_file": (appendix_file.name, appendix_stream, "application/octet-stream")},
                timeout=180,
            )
        self._raise_for_error(response)
        return response.json()

    def confirm_mapping_rule(
        self,
        *,
        act_material_name: str,
        ledger_material_name: str,
        preferred_1c_name: str = "",
        comment: str = "",
        active: bool = True,
    ) -> dict:
        self._ensure_license()
        response = requests.post(
            f"{self.api_base_url}/v1/materials-writeoff/mapping-rules/confirm",
            headers=API_REQUEST_HEADERS,
            json={
                "act_material_name": act_material_name,
                "ledger_material_name": ledger_material_name,
                "preferred_1c_name": preferred_1c_name or None,
                "comment": comment or None,
                "active": active,
            },
            timeout=30,
        )
        self._raise_for_error(response)
        return response.json()

    @staticmethod
    def pretty_json(payload: dict) -> str:
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _request_workbook(
        self,
        *,
        ledger_file: Path,
        act_file: Path | None,
        appendix_files: list[Path],
        mode: Mode,
    ) -> bytes:
        if mode == "standard":
            if act_file is None:
                raise ValueError("Не выбран файл акта.")
            endpoint = "/v1/materials-writeoff/process-files-workbook"
            with act_file.open("rb") as act_stream, ledger_file.open("rb") as ledger_stream:
                response = requests.post(
                    f"{self.api_base_url}{endpoint}",
                    headers=API_REQUEST_HEADERS,
                    files={
                        "act_file": (
                            act_file.name,
                            act_stream,
                            "application/octet-stream",
                        ),
                        "ledger_file": (
                            ledger_file.name,
                            ledger_stream,
                            "application/octet-stream",
                        ),
                    },
                    data={"enable_ai": "true"},
                    timeout=180,
                )
        else:
            if not appendix_files:
                raise ValueError("Не выбраны файлы приложений smart contract.")
            endpoint = "/v1/materials-writeoff/process-smart-contract-workbook"
            streams = [path.open("rb") for path in appendix_files]
            try:
                files: list[tuple[str, tuple[str, object, str]]] = [
                    (
                        "appendix_files",
                        (path.name, stream, "application/octet-stream"),
                    )
                    for path, stream in zip(appendix_files, streams, strict=True)
                ]
                with ledger_file.open("rb") as ledger_stream:
                    files.append(
                        (
                            "ledger_file",
                            (ledger_file.name, ledger_stream, "application/octet-stream"),
                        )
                    )
                    response = requests.post(
                        f"{self.api_base_url}{endpoint}",
                        headers=API_REQUEST_HEADERS,
                        files=files,
                        data={"enable_ai": "true"},
                        timeout=300,
                    )
            finally:
                for stream in streams:
                    stream.close()
        self._raise_for_error(response)
        return response.content

    @staticmethod
    def _raise_for_error(response: requests.Response) -> None:
        if response.ok:
            return
        try:
            payload = response.json()
            detail = payload.get("detail") or payload.get("message") or str(payload)
        except Exception:
            detail = response.text
        raise RuntimeError(detail)

    def _append_history(self, record: RunHistoryRecord) -> None:
        limit = self.settings_service.load().history_limit
        self.history_service.append(record, limit=limit)

    def _ensure_license(self) -> None:
        if self.license_service is not None:
            self.license_service.ensure_valid_or_raise()
