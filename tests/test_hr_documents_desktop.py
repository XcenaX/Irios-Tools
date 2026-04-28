from __future__ import annotations

import base64
from pathlib import Path

from desktop_app.services.hr_documents_service import HRDocumentsService


class _FakeLicenseService:
    def load_config(self):
        return type(
            "Config",
            (),
            {
                "license_key": "demo-key",
                "api_base_url": "http://127.0.0.1:8000",
                "token": "token",
                "device_id": "device-id",
            },
        )()

    def ensure_valid_or_raise(self):
        return None


class _FakeHistoryService:
    def append(self, record, *, limit: int) -> None:
        self.last_record = record
        self.last_limit = limit


class _FakeSettingsService:
    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def load(self):
        return type("Settings", (), {"output_dir": str(self._output_dir), "history_limit": 10})()


def test_save_documents_writes_docx_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "generated"
    documents = {
        "hire_order": {
            "generated": True,
            "filename": "hire_order.docx",
            "content_base64": base64.b64encode(b"docx-content").decode("ascii"),
        },
        "employment_contract": {
            "generated": True,
            "filename": "contract.docx",
            "content_base64": base64.b64encode(b"contract-content").decode("ascii"),
        },
        "vacation_registry": {
            "generated": True,
            "filename": "vacation_registry.xlsx",
            "content_base64": base64.b64encode(b"xlsx-content").decode("ascii"),
        },
        "unsupported": {
            "generated": False,
        },
    }

    saved = HRDocumentsService._save_documents(output_dir, documents)

    assert [path.name for path in saved] == ["hire_order.docx", "contract.docx", "vacation_registry.xlsx"]
    assert (output_dir / "hire_order.docx").read_bytes() == b"docx-content"
    assert (output_dir / "contract.docx").read_bytes() == b"contract-content"
    assert (output_dir / "vacation_registry.xlsx").read_bytes() == b"xlsx-content"


def test_default_output_dir_uses_settings_folder(tmp_path: Path) -> None:
    service = HRDocumentsService(
        license_service=_FakeLicenseService(),
        history_service=_FakeHistoryService(),
        settings_service=_FakeSettingsService(tmp_path),
    )

    output_dir = service.default_output_dir("isb_engineering")

    assert output_dir.parent.name == "isb_engineering"
    assert str(output_dir).startswith(str(tmp_path))
