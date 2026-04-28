from __future__ import annotations

import json

from shared import license_client
from shared.app_license import TOKEN_FILE_NAME
from shared.license_client import LicenseConfig, load_license_config, save_license_config


def test_license_config_ignores_stored_device_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(license_client, "compute_device_id", lambda: "current-device-id")
    monkeypatch.setattr(license_client, "get_device_name", lambda: "CURRENT-PC")
    monkeypatch.setattr(license_client, "load_user_license_token", lambda: "")
    (tmp_path / TOKEN_FILE_NAME).write_text(
        json.dumps(
            {
                "api_base_url": "http://example.test",
                "license_key": "KEY-1",
                "token": "token-1",
                "device_id": "copied-device-id",
                "device_name": "OLD-PC",
                "product_code": "missing_originals_app",
            }
        ),
        encoding="utf-8",
    )

    config = load_license_config(tmp_path)

    assert config.device_id == "current-device-id"
    assert config.device_name == "OLD-PC"


def test_license_config_persists_only_token_to_user_env(tmp_path, monkeypatch) -> None:
    saved_tokens: list[str] = []
    monkeypatch.setattr(license_client, "save_user_license_token", saved_tokens.append)

    path = save_license_config(
        tmp_path,
        LicenseConfig(
            api_base_url="http://example.test",
            license_key="KEY-1",
            token="token-1",
            device_id="runtime-only-device-id",
            device_name="CURRENT-PC",
            product_code="missing_originals_app",
        ),
    )

    assert path == tmp_path / TOKEN_FILE_NAME
    assert saved_tokens == ["token-1"]
    assert not path.exists()


def test_license_config_prefers_user_env_token(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(license_client, "compute_device_id", lambda: "current-device-id")
    monkeypatch.setattr(license_client, "load_user_license_token", lambda: "env-token")
    (tmp_path / TOKEN_FILE_NAME).write_text(
        json.dumps({"token": "file-token"}),
        encoding="utf-8",
    )

    config = load_license_config(tmp_path)

    assert config.token == "env-token"
