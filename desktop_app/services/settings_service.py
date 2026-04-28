from __future__ import annotations

import json
from dataclasses import asdict

from desktop_app.config.paths import settings_file_path
from desktop_app.state.models import AppSettings


class SettingsService:
    def load(self) -> AppSettings:
        path = settings_file_path()
        if not path.exists():
            return AppSettings()
        payload = json.loads(path.read_text(encoding="utf-8"))
        return AppSettings(**payload)

    def save(self, settings: AppSettings) -> None:
        path = settings_file_path()
        path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")
