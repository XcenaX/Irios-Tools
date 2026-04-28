from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def _find_row_value(df: pd.DataFrame, label: str) -> str:
    target = label.casefold()
    for _, row in df.iterrows():
        values = [_clean(value) for value in row.tolist()]
        for idx, value in enumerate(values):
            if value.casefold() == target:
                for candidate in values[idx + 1 :]:
                    if candidate:
                        return candidate
    return ""


def _find_contact_value(df: pd.DataFrame, label: str) -> str:
    target = label.casefold()
    for _, row in df.iterrows():
        values = [_clean(value) for value in row.tolist()]
        if len(values) >= 2 and values[0].casefold() == target and values[1]:
            return values[1]
    return ""


def _find_responsible_person(df: pd.DataFrame, role: str) -> tuple[str, str]:
    target = role.casefold()
    for _, row in df.iterrows():
        values = [_clean(value) for value in row.tolist()]
        if values and values[0].casefold() == target:
            full_name = values[2] if len(values) > 2 else ""
            position = values[3] if len(values) > 3 else ""
            return full_name, position
    return "", ""


def parse_organization_card(path: Path) -> dict[str, str]:
    df = pd.read_excel(path, sheet_name=0, header=None)
    director_name, director_position = _find_responsible_person(df, "Руководитель")
    short_name = _find_row_value(df, "Наименование (краткое):")
    full_name = _find_row_value(df, "Наименование (полное):")
    bank = _find_row_value(df, "Наименование")
    return {
        "organization_name": short_name or full_name,
        "employer_name": full_name,
        "employer_short_name": short_name,
        "employer_display_name": short_name.replace("ТОО", "").replace("«", "").replace("»", "").replace('"', "").strip() if short_name else "",
        "employer_bin": _find_row_value(df, "БИН / ИИН"),
        "employer_iik": _find_row_value(df, "Номер счета:"),
        "employer_bank": bank,
        "employer_bik": _find_row_value(df, "БИК"),
        "employer_legal_address": _find_contact_value(df, "Юридический адрес организации"),
        "employer_director_name": director_name,
        "employer_director_position": director_position,
    }
