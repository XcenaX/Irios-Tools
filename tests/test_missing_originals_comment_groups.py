from __future__ import annotations

from shared.missing_originals import extract_comment_group, split_report_rows_by_comment_group
from shared.missing_originals_contract import build_report_data_from_payload


def test_extract_comment_group_accepts_only_entire_numeric_comment() -> None:
    assert extract_comment_group("") is None
    assert extract_comment_group("гпх") is None
    assert extract_comment_group(" 2 ") == "2"
    assert extract_comment_group("дослать 15 оригиналов") is None
    assert extract_comment_group("08.02.2026") is None
    assert extract_comment_group("100%") is None


def test_split_report_rows_by_comment_group_keeps_common_report_and_digit_reports() -> None:
    payload = {
        "company_name": "Тестовая компания",
        "period_label": "01.01.2026 - 31.01.2026",
        "receipts": [
            {
                "index": 1,
                "counterparty": "Альфа",
                "date": "2026-01-10",
                "amount": 1000,
                "operation_type": "Поступление",
                "account_number": "A-1",
            },
            {
                "index": 2,
                "counterparty": "Бета",
                "date": "2026-01-11",
                "amount": 2000,
                "operation_type": "Поступление",
                "account_number": "A-2",
                "comment_group": "2",
            },
        ],
        "sales": [
            {
                "index": 1,
                "counterparty": "Гамма",
                "date": "2026-01-12",
                "amount": 3000,
                "operation_type": "Реализация",
                "account_number": "S-1",
                "comment_group": "1",
            },
            {
                "index": 2,
                "counterparty": "Дельта",
                "date": "2026-01-13",
                "amount": 4000,
                "operation_type": "Реализация",
                "account_number": "S-2",
                "comment_group": "2",
            },
        ],
    }

    report_data = build_report_data_from_payload(payload)
    grouped_reports = split_report_rows_by_comment_group(report_data)

    assert [group_key for group_key, _ in grouped_reports] == [None, "1", "2"]

    common_report = grouped_reports[0][1]
    assert [row["counterparty"] for row in common_report["receipts_rows"]] == ["Альфа"]
    assert common_report["sales_rows"] == []

    group_one_report = grouped_reports[1][1]
    assert [row["counterparty"] for row in group_one_report["sales_rows"]] == ["Гамма"]
    assert group_one_report["sales_rows"][0]["index"] == 1

    group_two_report = grouped_reports[2][1]
    assert [row["counterparty"] for row in group_two_report["receipts_rows"]] == ["Бета"]
    assert [row["counterparty"] for row in group_two_report["sales_rows"]] == ["Дельта"]
    assert group_two_report["receipts_rows"][0]["index"] == 1
    assert group_two_report["sales_rows"][0]["index"] == 1
