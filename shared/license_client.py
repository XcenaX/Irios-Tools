from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import uuid
from typing import Any
import ctypes

if os.name == "nt":
    import winreg
else:
    winreg = None  # type: ignore[assignment]

import requests

from .app_license import PRODUCT_CODE as APP_LICENSE_PRODUCT_CODE, TOKEN_FILE_NAME
from .missing_originals import DEFAULT_API_BASE_URL
from .missing_originals_contract import PRODUCT_CODE as MISSING_ORIGINALS_PRODUCT_CODE


CONFIG_VERSION = 1
TOKEN_ENV_VAR = "IRIOS_DESKTOP_LICENSE_TOKEN"
API_REQUEST_HEADERS = {"ngrok-skip-browser-warning": "true"}


@dataclass
class LicenseConfig:
    api_base_url: str = DEFAULT_API_BASE_URL
    license_key: str = ""
    token: str = ""
    device_id: str = ""
    device_name: str = ""
    product_code: str = APP_LICENSE_PRODUCT_CODE


class LicenseClientError(RuntimeError):
    pass


def default_config_path(base_dir: Path, token_file_name: str = TOKEN_FILE_NAME) -> Path:
    return base_dir / token_file_name


def get_device_name() -> str:
    return os.environ.get("COMPUTERNAME") or platform.node() or "unknown-device"


def _read_machine_guid() -> str:
    if os.name != "nt" or winreg is None:
        return ""
    key_path = r"SOFTWARE\Microsoft\Cryptography"
    access_modes = (
        winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0),
        winreg.KEY_READ,
    )
    for access in access_modes:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, access) as key:
                value, _ = winreg.QueryValueEx(key, "MachineGuid")
                return str(value).strip()
        except OSError:
            continue
    return _read_machine_guid_legacy()


def _read_machine_guid_legacy() -> str:
    try:
        import subprocess

        startupinfo = None
        creationflags = 0
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        output = subprocess.check_output(
            [
                "reg",
                "query",
                r"HKLM\SOFTWARE\Microsoft\Cryptography",
                "/v",
                "MachineGuid",
            ],
            text=True,
            encoding="utf-8",
            errors="ignore",
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
    except Exception:
        return ""
    for line in output.splitlines():
        if "MachineGuid" in line:
            return line.split()[-1].strip()
    return ""


def compute_device_id() -> str:
    parts = [
        _read_machine_guid(),
        get_device_name(),
        platform.platform(),
        hex(uuid.getnode()),
    ]
    normalized = "|".join(part for part in parts if part)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load_license_config(base_dir: Path, token_file_name: str = TOKEN_FILE_NAME) -> LicenseConfig:
    path = default_config_path(base_dir, token_file_name)
    device_id = compute_device_id()
    if not path.exists():
        return LicenseConfig(token=load_user_license_token(), device_id=device_id, device_name=get_device_name())

    data = json.loads(path.read_text(encoding="utf-8"))
    return LicenseConfig(
        api_base_url=data.get("api_base_url", DEFAULT_API_BASE_URL),
        license_key=data.get("license_key", ""),
        token=load_user_license_token() or data.get("token", ""),
        device_id=device_id,
        device_name=data.get("device_name", get_device_name()),
        product_code=data.get("product_code", APP_LICENSE_PRODUCT_CODE),
    )


def save_license_config(
    base_dir: Path,
    config: LicenseConfig,
    token_file_name: str = TOKEN_FILE_NAME,
) -> Path:
    save_user_license_token(config.token)
    path = default_config_path(base_dir, token_file_name)
    return path


def load_user_license_token() -> str:
    token = os.environ.get(TOKEN_ENV_VAR, "").strip()
    if token or os.name != "nt":
        return token
    try:
        assert winreg is not None
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _ = winreg.QueryValueEx(key, TOKEN_ENV_VAR)
    except OSError:
        return ""
    return str(value).strip()


def save_user_license_token(token: str) -> None:
    token = token.strip()
    if token:
        os.environ[TOKEN_ENV_VAR] = token
    else:
        os.environ.pop(TOKEN_ENV_VAR, None)
    if os.name != "nt":
        return
    assert winreg is not None
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
        if token:
            winreg.SetValueEx(key, TOKEN_ENV_VAR, 0, winreg.REG_SZ, token)
        else:
            try:
                winreg.DeleteValue(key, TOKEN_ENV_VAR)
            except FileNotFoundError:
                pass
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0, 5000, None)


def activate_license(
    *,
    api_base_url: str,
    license_key: str,
    device_id: str,
    device_name: str,
    app_version: str,
    product_code: str = APP_LICENSE_PRODUCT_CODE,
    timeout: float = 15.0,
) -> dict[str, Any]:
    response = requests.post(
        f"{api_base_url.rstrip('/')}/v1/license/activate",
        headers=API_REQUEST_HEADERS,
        json={
            "license_key": license_key,
            "product_code": product_code,
            "device_id": device_id,
            "device_name": device_name,
            "app_version": app_version,
        },
        timeout=timeout,
    )
    _raise_for_error(response)
    return response.json()


def check_license(
    *,
    api_base_url: str,
    token: str,
    device_id: str,
    app_version: str,
    timeout: float = 15.0,
) -> dict[str, Any]:
    response = requests.post(
        f"{api_base_url.rstrip('/')}/v1/license/check",
        headers=API_REQUEST_HEADERS,
        json={
            "token": token,
            "device_id": device_id,
            "app_version": app_version,
        },
        timeout=timeout,
    )
    _raise_for_error(response)
    return response.json()


def build_report_via_api(
    *,
    api_base_url: str,
    token: str,
    device_id: str,
    payload_version: int,
    payload: dict[str, Any],
    timeout: float = 60.0,
) -> dict[str, Any]:
    response = requests.post(
        f"{api_base_url.rstrip('/')}/v1/products/{MISSING_ORIGINALS_PRODUCT_CODE}/build",
        headers=API_REQUEST_HEADERS,
        json={
            "token": token,
            "device_id": device_id,
            "payload_version": payload_version,
            "payload": payload,
        },
        timeout=timeout,
    )
    _raise_for_error(response)
    return response.json()


def build_hr_documents_via_api(
    *,
    api_base_url: str,
    token: str,
    device_id: str,
    payload_version: int,
    payload: dict[str, Any],
    product_code: str,
    timeout: float = 60.0,
) -> dict[str, Any]:
    response = requests.post(
        f"{api_base_url.rstrip('/')}/v1/products/{product_code}/build",
        headers=API_REQUEST_HEADERS,
        json={
            "token": token,
            "device_id": device_id,
            "payload_version": payload_version,
            "payload": payload,
        },
        timeout=timeout,
    )
    _raise_for_error(response)
    return response.json()


def _raise_for_error(response: requests.Response) -> None:
    if response.ok:
        return
    try:
        payload = response.json()
    except Exception:
        payload = {"detail": response.text}
    detail = payload.get("detail") or payload.get("message") or str(payload)
    raise LicenseClientError(detail)
