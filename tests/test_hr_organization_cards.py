from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from shared.hr_organization_cards import parse_organization_card


def test_parse_organization_card_extracts_core_fields(tmp_path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    rows = [
        ["", "Наименование (краткое):", "", "", "", "", "", "", 'ТОО "Gefest Consortium"'],
        ["", "Наименование (полное):", "", "", "", "", "", "", 'Товарищество с ограниченной ответственностью "Gefest Consortium"'],
        ["", "БИН / ИИН", "", "", "", "", "", "", "140440010891"],
        ["", "Номер счета:", "", "", "", "KZ108562203116393975"],
        ["", "Наименование", "", "", "", 'АО "Банк ЦентрКредит"'],
        ["", "БИК", "", "", "", "KCJBKZKX"],
        ["Юридический адрес организации", "130000, Республика Казахстан, г. Астана, ул. Пушкина, дом 15, к. 135"],
        ["Руководитель", "1 января 2024 г.", "Алиев Салман Сулумбекович", "Генеральный директор"],
    ]
    for row in rows:
        sheet.append(row)
    path = tmp_path / "org_card.xlsx"
    workbook.save(path)

    parsed = parse_organization_card(path)
    assert parsed["organization_name"] == 'ТОО "Gefest Consortium"'
    assert parsed["employer_name"] == 'Товарищество с ограниченной ответственностью "Gefest Consortium"'
    assert parsed["employer_bin"] == "140440010891"
    assert parsed["employer_iik"] == "KZ108562203116393975"
    assert parsed["employer_bank"] == 'АО "Банк ЦентрКредит"'
    assert parsed["employer_bik"] == "KCJBKZKX"
    assert "Пушкина" in parsed["employer_legal_address"]
    assert parsed["employer_director_name"] == "Алиев Салман Сулумбекович"
    assert parsed["employer_director_position"] == "Генеральный директор"
