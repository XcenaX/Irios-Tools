from __future__ import annotations

from pathlib import Path

from desktop_app.services.materials_writeoff_service import MaterialsWriteoffService
from shared.license_client import API_REQUEST_HEADERS


class _FakeHistoryService:
    def append(self, record, *, limit: int) -> None:
        self.last_record = record
        self.last_limit = limit


class _FakeSettingsService:
    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def load(self):
        return type("Settings", (), {"output_dir": str(self._output_dir), "history_limit": 10})()


class _FakeLicenseService:
    def __init__(self) -> None:
        self.calls = 0

    def ensure_valid_or_raise(self) -> None:
        self.calls += 1


class _FakeResponse:
    def __init__(self, *, ok: bool = True, content: bytes = b"", text: str = "", payload: dict | None = None) -> None:
        self.ok = ok
        self.content = content
        self.text = text
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_default_output_file_uses_settings_folder(tmp_path: Path) -> None:
    service = MaterialsWriteoffService(
        settings_service=_FakeSettingsService(tmp_path),
        history_service=_FakeHistoryService(),
    )

    output_file = service.default_output_file("standard")

    assert str(output_file).startswith(str(tmp_path))
    assert output_file.suffix == ".xlsx"


def test_process_standard_files_writes_workbook(monkeypatch, tmp_path: Path) -> None:
    act_file = tmp_path / "act.xlsx"
    ledger_file = tmp_path / "ledger.xlsx"
    act_file.write_bytes(b"act")
    ledger_file.write_bytes(b"ledger")
    history = _FakeHistoryService()
    license_service = _FakeLicenseService()
    service = MaterialsWriteoffService(
        settings_service=_FakeSettingsService(tmp_path),
        history_service=history,
        license_service=license_service,
    )

    def fake_post(url, *, headers, files, data, timeout):  # noqa: ANN001
        assert url.endswith("/v1/materials-writeoff/process-files-workbook")
        assert headers == API_REQUEST_HEADERS
        assert "act_file" in files
        assert "ledger_file" in files
        assert data["enable_ai"] == "true"
        return _FakeResponse(content=b"xlsx-content")

    monkeypatch.setattr("desktop_app.services.materials_writeoff_service.requests.post", fake_post)

    result = service.process_files(ledger_file=ledger_file, act_file=act_file, mode="standard")

    assert result.output_file.exists()
    assert result.output_file.read_bytes() == b"xlsx-content"
    assert history.last_record.module_id == "materials_writeoff"
    assert history.last_record.status == "success"
    assert license_service.calls == 1


def test_process_smart_contract_files_writes_workbook(monkeypatch, tmp_path: Path) -> None:
    appendix_a = tmp_path / "appendix1.png"
    appendix_b = tmp_path / "appendix2.png"
    ledger_file = tmp_path / "ledger.xlsx"
    appendix_a.write_bytes(b"a")
    appendix_b.write_bytes(b"b")
    ledger_file.write_bytes(b"ledger")
    service = MaterialsWriteoffService(
        settings_service=_FakeSettingsService(tmp_path),
        history_service=_FakeHistoryService(),
    )

    def fake_post(url, *, headers, files, data, timeout):  # noqa: ANN001
        assert url.endswith("/v1/materials-writeoff/process-smart-contract-workbook")
        assert headers == API_REQUEST_HEADERS
        assert [item[0] for item in files].count("appendix_files") == 2
        assert any(item[0] == "ledger_file" for item in files)
        return _FakeResponse(content=b"smart-xlsx")

    monkeypatch.setattr("desktop_app.services.materials_writeoff_service.requests.post", fake_post)

    result = service.process_files(
        ledger_file=ledger_file,
        appendix_files=[appendix_a, appendix_b],
        mode="smart_contract",
    )

    assert result.output_file.exists()
    assert result.output_file.read_bytes() == b"smart-xlsx"


def test_match_files_calls_api(monkeypatch, tmp_path: Path) -> None:
    act_file = tmp_path / "act.xlsx"
    ledger_file = tmp_path / "ledger.xlsx"
    act_file.write_bytes(b"act")
    ledger_file.write_bytes(b"ledger")
    license_service = _FakeLicenseService()
    service = MaterialsWriteoffService(
        settings_service=_FakeSettingsService(tmp_path),
        history_service=_FakeHistoryService(),
        license_service=license_service,
    )

    def fake_post(url, *, headers, files, data, timeout):  # noqa: ANN001
        assert url.endswith("/v1/materials-writeoff/match-files")
        assert headers == API_REQUEST_HEADERS
        assert "act_file" in files
        assert "ledger_file" in files
        assert data["enable_ai"] == "true"
        return _FakeResponse(payload={"summary": {"total_rows": 1}})

    monkeypatch.setattr("desktop_app.services.materials_writeoff_service.requests.post", fake_post)

    result = service.match_files(act_file=act_file, ledger_file=ledger_file)

    assert result["summary"]["total_rows"] == 1
    assert license_service.calls == 1


def test_extract_act_pdf_calls_api(monkeypatch, tmp_path: Path) -> None:
    act_file = tmp_path / "act.pdf"
    act_file.write_bytes(b"pdf")
    service = MaterialsWriteoffService(
        settings_service=_FakeSettingsService(tmp_path),
        history_service=_FakeHistoryService(),
    )

    def fake_post(url, *, headers, files, timeout):  # noqa: ANN001
        assert url.endswith("/v1/materials-writeoff/extract-act-pdf")
        assert headers == API_REQUEST_HEADERS
        assert "act_file" in files
        return _FakeResponse(payload={"rows": [{"line_no": 1}], "raw_text_chars": 10})

    monkeypatch.setattr("desktop_app.services.materials_writeoff_service.requests.post", fake_post)

    result = service.extract_act_pdf(act_file)

    assert result["raw_text_chars"] == 10


def test_extract_smart_appendix_calls_api(monkeypatch, tmp_path: Path) -> None:
    appendix_file = tmp_path / "appendix.png"
    appendix_file.write_bytes(b"image")
    service = MaterialsWriteoffService(
        settings_service=_FakeSettingsService(tmp_path),
        history_service=_FakeHistoryService(),
    )

    def fake_post(url, *, headers, files, timeout):  # noqa: ANN001
        assert url.endswith("/v1/materials-writeoff/extract-smart-appendix")
        assert headers == API_REQUEST_HEADERS
        assert "appendix_file" in files
        return _FakeResponse(payload={"raw_rows": [], "aggregated_rows": []})

    monkeypatch.setattr("desktop_app.services.materials_writeoff_service.requests.post", fake_post)

    result = service.extract_smart_appendix(appendix_file)

    assert result["aggregated_rows"] == []


def test_confirm_mapping_rule_calls_api(monkeypatch, tmp_path: Path) -> None:
    service = MaterialsWriteoffService(
        settings_service=_FakeSettingsService(tmp_path),
        history_service=_FakeHistoryService(),
    )

    def fake_post(url, *, headers, json, timeout):  # noqa: ANN001
        assert url.endswith("/v1/materials-writeoff/mapping-rules/confirm")
        assert headers == API_REQUEST_HEADERS
        assert json["act_material_name"] == "Act coating"
        assert json["ledger_material_name"] == "Ledger coating"
        return _FakeResponse(payload={"created": True, "rules_count": 1})

    monkeypatch.setattr("desktop_app.services.materials_writeoff_service.requests.post", fake_post)

    result = service.confirm_mapping_rule(
        act_material_name="Act coating",
        ledger_material_name="Ledger coating",
    )

    assert result["created"] is True
