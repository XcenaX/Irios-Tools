from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class AppSettings:
    theme_mode: str = "system"
    api_base_url: str = ""
    output_dir: str = ""
    open_folder_after_success: bool = True
    history_limit: int = 30


@dataclass
class LicenseStatusSnapshot:
    is_active: bool
    status_text: str
    expires_at: str | None = None
    license_key: str = ""
    device_id: str = ""
    device_name: str = ""
    last_checked_at: str | None = None
    error: str = ""


@dataclass
class RunRequest:
    module_id: str
    receipts_file: Path
    sales_file: Path
    output_file: Path


@dataclass
class RunResult:
    module_id: str
    output_file: Path
    company_name: str
    receipts_count: int
    sales_count: int
    completed_at: str

    @property
    def total_count(self) -> int:
        return self.receipts_count + self.sales_count


@dataclass
class HRDocumentsRunResult:
    module_id: str
    output_dir: Path
    organization_code: str
    generated_files: list[Path]
    validation_errors: list[str]
    validation_warnings: list[str]
    completed_at: str


@dataclass
class MaterialsWriteoffRunResult:
    module_id: str
    output_file: Path
    mode: str
    completed_at: str


@dataclass
class RunHistoryRecord:
    module_id: str
    started_at: str
    status: str
    receipts_file: str = ""
    sales_file: str = ""
    output_file: str = ""
    message: str = ""
    company_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RunHistoryRecord":
        return cls(**payload)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
