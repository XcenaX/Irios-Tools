from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Callable

import requests

from desktop_app.config.app_info import APP_VERSION, UPDATE_MANIFEST_URL
from desktop_app.config.paths import user_data_dir
from shared.license_client import API_REQUEST_HEADERS


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    url: str
    sha256: str
    size: int = 0
    mandatory: bool = True
    message: str = "Подождите, программа обновляется"


class UpdateService:
    def __init__(self, *, manifest_url: str = UPDATE_MANIFEST_URL) -> None:
        self.manifest_url = manifest_url

    def should_check_updates(self) -> bool:
        return bool(self.manifest_url) and bool(getattr(sys, "frozen", False))

    def fetch_update_info(self) -> UpdateInfo | None:
        response = requests.get(
            self.manifest_url,
            headers={**API_REQUEST_HEADERS, "Cache-Control": "no-cache"},
            timeout=10,
        )
        response.raise_for_status()
        payload = json.loads(response.content.decode("utf-8-sig"))
        latest_version = str(payload.get("version", "")).strip()
        if not latest_version or _version_tuple(latest_version) <= _version_tuple(APP_VERSION):
            return None
        return UpdateInfo(
            version=latest_version,
            url=str(payload.get("url", "")).strip(),
            sha256=str(payload.get("sha256", "")).strip().lower(),
            size=int(payload.get("size") or 0),
            mandatory=bool(payload.get("mandatory", True)),
            message=str(payload.get("message") or "Подождите, программа обновляется"),
        )

    def download_update(
        self,
        update: UpdateInfo,
        *,
        progress: Callable[[int, int], None] | None = None,
    ) -> Path:
        if not update.url:
            raise RuntimeError("В manifest не указан URL обновления.")
        if not update.sha256:
            raise RuntimeError("В manifest не указан SHA256 обновления.")

        updates_dir = user_data_dir() / "updates"
        updates_dir.mkdir(parents=True, exist_ok=True)
        target = updates_dir / f"Irios Tools {update.version}.exe"
        temp_target = target.with_suffix(".exe.download")

        downloaded = 0
        hasher = hashlib.sha256()
        with requests.get(update.url, headers=API_REQUEST_HEADERS, stream=True, timeout=60) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length") or update.size or 0)
            with temp_target.open("wb") as stream:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    stream.write(chunk)
                    hasher.update(chunk)
                    downloaded += len(chunk)
                    if progress is not None:
                        progress(downloaded, total)

        actual_hash = hasher.hexdigest().lower()
        if actual_hash != update.sha256:
            temp_target.unlink(missing_ok=True)
            raise RuntimeError("Контрольная сумма обновления не совпала.")

        temp_target.replace(target)
        return target

    def create_updater_script(self, downloaded_exe: Path) -> Path:
        if not getattr(sys, "frozen", False):
            raise RuntimeError("Обновление доступно только для собранного EXE.")
        target_exe = Path(sys.executable).resolve()
        script_path = user_data_dir() / "updates" / "apply_update.ps1"
        backup_path = target_exe.with_suffix(target_exe.suffix + ".bak")
        script = f"""
$ErrorActionPreference = "Stop"
$ProcessIdToWait = {os.getpid()}
$TargetPath = {_ps_quote(target_exe)}
$NewPath = {_ps_quote(downloaded_exe)}
$BackupPath = {_ps_quote(backup_path)}

try {{
    Wait-Process -Id $ProcessIdToWait -Timeout 60 -ErrorAction SilentlyContinue
}} catch {{}}

Start-Sleep -Milliseconds 700

if (Test-Path -LiteralPath $BackupPath) {{
    Remove-Item -LiteralPath $BackupPath -Force
}}

try {{
    if (Test-Path -LiteralPath $TargetPath) {{
        Move-Item -LiteralPath $TargetPath -Destination $BackupPath -Force
    }}

    Copy-Item -LiteralPath $NewPath -Destination $TargetPath -Force
    Start-Process -FilePath $TargetPath
}} catch {{
    if ((-not (Test-Path -LiteralPath $TargetPath)) -and (Test-Path -LiteralPath $BackupPath)) {{
        Move-Item -LiteralPath $BackupPath -Destination $TargetPath -Force
    }}
    throw
}}
"""
        script_path.write_text(script.strip() + "\n", encoding="utf-8")
        return script_path

    def launch_updater(self, script_path: Path) -> None:
        subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
            ],
            close_fds=True,
        )


def _version_tuple(value: str) -> tuple[int, ...]:
    parts = [int(part) for part in re.findall(r"\d+", value)]
    return tuple(parts or [0])


def _ps_quote(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"
