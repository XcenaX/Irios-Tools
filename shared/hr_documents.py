from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any

import pandas as pd


def _resource_root() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


REPO_ROOT = _resource_root()
DATA_DIR = REPO_ROOT / "data"


@dataclass(frozen=True)
class T2ParseResult:
    raw_fields: dict[str, Any]
    job_history: list[dict[str, Any]]
    vacation_history: list[dict[str, Any]]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_hr_field_mapping() -> dict[str, Any]:
    return _load_json(DATA_DIR / "hr_field_mapping.json")


def load_hr_organizations() -> dict[str, Any]:
    return _load_json(DATA_DIR / "hr_organizations.json")


def load_hr_contract_templates() -> dict[str, Any]:
    return _load_json(DATA_DIR / "hr_contract_templates.json")


def load_hr_rules() -> dict[str, Any]:
    return _load_json(DATA_DIR / "hr_rules.json")


def load_kz_holidays(year: int) -> dict[str, Any]:
    return _load_json(DATA_DIR / f"kz_holidays_{year}.json")


def _cell(df: pd.DataFrame, row: int, col: int) -> str:
    value = df.iat[row, col]
    if pd.isna(value):
        return ""
    return str(value).strip()


def _parse_date(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def _money(value: str) -> str:
    digits = re.sub(r"[^\d,.\-]", "", value)
    if not digits:
        return ""
    normalized = digits.replace(",", ".")
    try:
        amount = float(normalized)
    except ValueError:
        return ""
    if amount.is_integer():
        return str(int(amount))
    return f"{amount:.2f}".rstrip("0").rstrip(".")


def _compose_birth_date(df: pd.DataFrame) -> str:
    year = _cell(df, 22, 4)
    day = _cell(df, 22, 6)
    month = _cell(df, 22, 7)
    if not (year and day and month):
        return ""
    try:
        return datetime(int(year), int(month), int(day)).date().isoformat()
    except ValueError:
        return ""


def _parse_id_doc_type(df: pd.DataFrame) -> str:
    raw = _cell(df, 36, 10)
    if ":" not in raw:
        return raw
    return raw.split(":", 1)[1].strip()


def _parse_id_doc_number(df: pd.DataFrame) -> str:
    prefix = _cell(df, 37, 10)
    number = _cell(df, 37, 11)
    return " ".join(part for part in (prefix, number) if part).strip()


def _parse_job_history(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in range(63, 74):
        date_value = _parse_date(_cell(df, row, 1))
        if not date_value:
            continue
        rows.append(
            {
                "date": date_value,
                "department": _cell(df, row, 3),
                "position": _cell(df, row, 5),
                "salary": _money(_cell(df, row, 8)),
                "basis": _cell(df, row, 11),
            }
        )
    return rows


def _parse_vacation_history(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in range(79, 89):
        start_date = _parse_date(_cell(df, row, 6))
        end_date = _parse_date(_cell(df, row, 8))
        if not (start_date or end_date):
            continue
        basis = _cell(df, row, 11)
        rows.append(
            {
                "vacation_kind": _cell(df, row, 1),
                "vacation_start_date": start_date,
                "vacation_end_date": end_date,
                "basis": basis,
                "vacation_days": _extract_vacation_days(basis),
            }
        )
    return rows


def _extract_vacation_days(value: str) -> int | None:
    text = str(value or "").strip().lower()
    if not text:
        return None
    patterns = (
        r"(\d+)\s*к\.\s*д",
        r"(\d+)\s*кд",
        r"(\d+)\s*календар",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def parse_t2_file(path: Path) -> T2ParseResult:
    df = pd.read_excel(path, sheet_name=0, header=None)
    job_history = _parse_job_history(df)
    latest_job = job_history[-1] if job_history else {}
    first_job = job_history[0] if job_history else {}
    raw_fields = {
        "t2_card_number": _cell(df, 12, 5),
        "t2_created_at": _parse_date(_cell(df, 15, 1)),
        "t2_personnel_number": _cell(df, 15, 3),
        "t2_last_name": _cell(df, 18, 3),
        "t2_first_name": _cell(df, 19, 3),
        "t2_middle_name": _cell(df, 21, 2) or _cell(df, 21, 3),
        "t2_birth_date": _compose_birth_date(df),
        "t2_birth_place": _cell(df, 23, 3),
        "t2_citizenship": _cell(df, 24, 3),
        "t2_id_doc_type": _parse_id_doc_type(df),
        "t2_id_doc_number": _parse_id_doc_number(df),
        "t2_id_doc_issuer": _cell(df, 38, 12),
        "t2_id_doc_issue_date": _parse_date(_cell(df, 39, 12)),
        "t2_home_address": _cell(df, 40, 11) or _cell(df, 41, 11) or _cell(df, 42, 12),
        "t2_phone": _cell(df, 42, 11),
        "t2_employment_start_date": first_job.get("date", ""),
        "t2_current_department": latest_job.get("department", ""),
        "t2_current_position": latest_job.get("position", ""),
        "t2_current_salary": latest_job.get("salary", ""),
        "t2_current_assignment_basis": latest_job.get("basis", ""),
    }
    return T2ParseResult(
        raw_fields=raw_fields,
        job_history=job_history,
        vacation_history=_parse_vacation_history(df),
    )


def build_hr_documents_payload(
    *,
    t2_file: Path,
    organization_code: str,
    contract_template_code: str | None = None,
    salary_clause_mode: str | None = None,
    manual_values: dict[str, Any] | None = None,
    document_requests: list[str] | None = None,
) -> dict[str, Any]:
    parsed = parse_t2_file(t2_file)
    return {
        "organization_code": organization_code,
        "contract_template_code": contract_template_code,
        "salary_clause_mode": salary_clause_mode,
        "document_requests": document_requests or ["employment_contract", "hire_order"],
        "raw_fields": parsed.raw_fields,
        "job_history": parsed.job_history,
        "vacation_history": parsed.vacation_history,
        "manual_values": manual_values or {},
    }
