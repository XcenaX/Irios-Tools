from __future__ import annotations

from pathlib import Path

import pandas as pd

from shared.missing_originals import resolve_column_name


def test_resolve_original_column_accepts_plural_receipts_header() -> None:
    df = pd.DataFrame(
        columns=[
            "Индикатор ошибки",
            "Оригинал документов (Поступления ТМЗ и услуг)",
            "Дата",
        ]
    )

    column = resolve_column_name(
        df,
        preferred_names=("Оригинал документа (Поступления ТМЗ и услуг)",),
        fallback_index=None,
        label="Оригинал",
        path=Path("receipts.xls"),
        required=True,
        contains_keywords=("оригинал",),
    )

    assert column == "Оригинал документов (Поступления ТМЗ и услуг)"


def test_resolve_original_column_accepts_sales_link_header() -> None:
    df = pd.DataFrame(
        columns=[
            "Оригинал документа (Реализация ТМЗ и услуг) (Ссылка)",
            "Дата",
            "Сумма",
        ]
    )

    column = resolve_column_name(
        df,
        preferred_names=("Оригинал", "Оригинал документов (Реализации ТМЗ и услуг)"),
        fallback_index=None,
        label="Оригинал",
        path=Path("sales.xls"),
        required=True,
        contains_keywords=("оригинал",),
    )

    assert column == "Оригинал документа (Реализация ТМЗ и услуг) (Ссылка)"
