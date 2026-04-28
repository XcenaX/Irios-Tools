from __future__ import annotations

from desktop_app.services import update_service
from desktop_app.services.update_service import UpdateService


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_fetch_update_info_returns_none_for_current_version(monkeypatch) -> None:
    monkeypatch.setattr(
        update_service.requests,
        "get",
        lambda *_, **__: _FakeResponse({"version": update_service.APP_VERSION}),
    )

    assert UpdateService(manifest_url="https://example.test/latest.json").fetch_update_info() is None


def test_fetch_update_info_detects_newer_version(monkeypatch) -> None:
    monkeypatch.setattr(
        update_service.requests,
        "get",
        lambda *_, **__: _FakeResponse(
            {
                "version": "99.0.0",
                "url": "https://example.test/Irios.Tools.exe",
                "sha256": "abc123",
                "size": 123,
                "message": "Обновление",
            }
        ),
    )

    update = UpdateService(manifest_url="https://example.test/latest.json").fetch_update_info()

    assert update is not None
    assert update.version == "99.0.0"
    assert update.url == "https://example.test/Irios.Tools.exe"
    assert update.sha256 == "abc123"
