from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


PRODUCT_CODE = "missing_originals"
PRODUCT_VERSION = 1


def _parse_row_date(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _collapse_spaces(value: str) -> str:
    return " ".join(value.split())


def _normalize_payload_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for position, row in enumerate(rows, start=1):
        parsed_date = _parse_row_date(str(row["date"]))
        normalized.append(
            {
                "index": position,
                "counterparty": _collapse_spaces(str(row["counterparty"]).strip()),
                "date": parsed_date.date().isoformat(),
                "amount": float(row["amount"]),
                "operation_type": _collapse_spaces(str(row.get("operation_type", "")).strip()),
                "account_number": _collapse_spaces(str(row.get("account_number", "")).strip()),
                "comment_group": str(row.get("comment_group", "")).strip() or None,
            }
        )
    normalized.sort(
        key=lambda item: (
            item["date"],
            item["counterparty"].casefold(),
            item["amount"],
            item["operation_type"].casefold(),
            item["account_number"].casefold(),
        )
    )
    for idx, row in enumerate(normalized, start=1):
        row["index"] = idx
    return normalized


def build_report_data_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    receipts = _normalize_payload_rows(list(payload.get("receipts", [])))
    sales = _normalize_payload_rows(list(payload.get("sales", [])))
    receipts_total = sum(float(row["amount"]) for row in receipts)
    sales_total = sum(float(row["amount"]) for row in sales)
    return {
        "company_name": str(payload["company_name"]),
        "period_label": str(payload["period_label"]),
        "receipts_rows": receipts,
        "sales_rows": sales,
        "totals": {
            "receipts_count": len(receipts),
            "sales_count": len(sales),
            "total_count": len(receipts) + len(sales),
            "receipts_amount": receipts_total,
            "sales_amount": sales_total,
        },
        "generated_at": datetime.now(UTC).isoformat(),
    }
