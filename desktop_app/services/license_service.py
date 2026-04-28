from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from desktop_app.config.app_info import APP_VERSION
from desktop_app.config.paths import user_data_dir
from desktop_app.state.models import LicenseStatusSnapshot
from shared.app_license import PRODUCT_CODE as APP_PRODUCT_CODE, TOKEN_FILE_NAME as APP_TOKEN_FILE_NAME
from shared.license_client import (
    LicenseClientError,
    LicenseConfig,
    activate_license,
    check_license,
    compute_device_id,
    get_device_name,
    load_license_config,
    save_license_config,
)
from shared.missing_originals import DEFAULT_API_BASE_URL

LEGACY_TOKEN_FILE_NAMES = (".missing_originals_license.json", ".hr_documents_license.json")


@dataclass
class ActivationResult:
    snapshot: LicenseStatusSnapshot
    config: LicenseConfig


def humanize_error_message(text: str) -> str:
    lowered = text.casefold()
    if "string_too_short" in lowered or "at least 4 characters" in lowered:
        return "Введите корректный ключ лицензии."
    if "failed to establish a new connection" in lowered or "max retries exceeded" in lowered:
        return "API недоступен. Проверьте, что сервер запущен и указан правильный адрес API."
    if "invalid token signature" in lowered:
        return "Сеанс недействителен. Выполните повторную активацию лицензии."
    if "subscription expired" in lowered:
        return "Подписка истекла. Обратитесь к администратору для продления."
    if "device mismatch" in lowered:
        return "Лицензия привязана к другому устройству."
    if "not activated" in lowered:
        return "Это устройство не активировано для текущей лицензии."
    if "invalid token payload" in lowered or "invalid token format" in lowered:
        return "Лицензионные данные повреждены. Выполните повторную активацию."
    if "field required" in lowered:
        return "Не заполнены обязательные поля для проверки лицензии."
    return text


def infer_status_label(message: str) -> str:
    lowered = message.casefold()
    if "api недоступен" in lowered:
        return "API недоступен"
    if "активац" in lowered:
        return "Требуется активация"
    if "подписка истекла" in lowered:
        return "Подписка истекла"
    return "Ошибка доступа"


class LicenseService:
    def __init__(
        self,
        *,
        base_dir: Path | None = None,
        api_base_url: str | None = None,
        product_code: str = APP_PRODUCT_CODE,
        token_file_name: str = APP_TOKEN_FILE_NAME,
    ) -> None:
        self.base_dir = base_dir or user_data_dir()
        self.api_base_url = (api_base_url or DEFAULT_API_BASE_URL).rstrip("/")
        self.product_code = product_code
        self.token_file_name = token_file_name

    def load_config(self) -> LicenseConfig:
        config = load_license_config(self.base_dir, self.token_file_name)
        if not config.token and self.token_file_name == APP_TOKEN_FILE_NAME:
            config = self._load_legacy_config() or config
        config.api_base_url = self.api_base_url or config.api_base_url
        config.device_id = compute_device_id()
        config.device_name = config.device_name or get_device_name()
        config.product_code = self.product_code
        return config

    def save_config(self, config: LicenseConfig) -> None:
        config.product_code = self.product_code
        save_license_config(self.base_dir, config, self.token_file_name)

    def _load_legacy_config(self) -> LicenseConfig | None:
        for token_file_name in LEGACY_TOKEN_FILE_NAMES:
            legacy_path = self.base_dir / token_file_name
            if legacy_path.exists():
                legacy_config = load_license_config(self.base_dir, token_file_name)
                if legacy_config.token:
                    self.save_config(legacy_config)
                    return legacy_config
        return None

    def get_snapshot(self) -> LicenseStatusSnapshot:
        config = self.load_config()
        if not config.token:
            return LicenseStatusSnapshot(
                is_active=False,
                status_text="Требуется активация",
                license_key=config.license_key,
                device_id=config.device_id,
                device_name=config.device_name,
            )
        try:
            response = check_license(
                api_base_url=config.api_base_url,
                token=config.token,
                device_id=config.device_id,
                app_version=APP_VERSION,
            )
            return LicenseStatusSnapshot(
                is_active=response.get("license_status") == "active",
                status_text=self._status_text(response.get("license_status", "unknown")),
                expires_at=response.get("expires_at"),
                license_key=config.license_key,
                device_id=config.device_id,
                device_name=config.device_name,
                last_checked_at=datetime.now().isoformat(timespec="seconds"),
            )
        except Exception as exc:
            message = humanize_error_message(str(exc))
            return LicenseStatusSnapshot(
                is_active=False,
                status_text=infer_status_label(message),
                license_key=config.license_key,
                device_id=config.device_id,
                device_name=config.device_name,
                last_checked_at=datetime.now().isoformat(timespec="seconds"),
                error=message,
            )

    def activate(self, license_key: str) -> ActivationResult:
        config = self.load_config()
        config.license_key = license_key.strip()
        if len(config.license_key) < 4:
            raise LicenseClientError("Введите корректный ключ лицензии.")
        try:
            response = activate_license(
                api_base_url=config.api_base_url,
                license_key=config.license_key,
                device_id=config.device_id,
                device_name=config.device_name,
                app_version=APP_VERSION,
                product_code=self.product_code,
            )
        except Exception as exc:
            raise LicenseClientError(humanize_error_message(str(exc))) from exc

        config.token = response["token"]
        self.save_config(config)
        snapshot = LicenseStatusSnapshot(
            is_active=True,
            status_text="Подписка активна",
            expires_at=response["license"].get("expires_at"),
            license_key=config.license_key,
            device_id=config.device_id,
            device_name=config.device_name,
            last_checked_at=datetime.now().isoformat(timespec="seconds"),
        )
        return ActivationResult(snapshot=snapshot, config=config)

    def ensure_valid_or_refresh(self) -> LicenseStatusSnapshot:
        config = self.load_config()
        snapshot = self.get_snapshot()
        if snapshot.is_active:
            return snapshot
        if not config.license_key:
            raise LicenseClientError(snapshot.error or snapshot.status_text)
        activation = self.activate(config.license_key)
        return activation.snapshot

    def ensure_valid_or_raise(self) -> LicenseStatusSnapshot:
        return self.ensure_valid_or_refresh()

    @staticmethod
    def _status_text(status: str) -> str:
        mapping = {
            "active": "Подписка активна",
            "expired": "Подписка истекла",
            "blocked": "Лицензия заблокирована",
        }
        return mapping.get(status, "Статус неизвестен")
