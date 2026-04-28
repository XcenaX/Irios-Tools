from __future__ import annotations

import json

from desktop_app.config.paths import history_file_path
from desktop_app.state.models import RunHistoryRecord


class HistoryService:
    def load(self) -> list[RunHistoryRecord]:
        path = history_file_path()
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [RunHistoryRecord.from_dict(item) for item in payload]

    def append(self, record: RunHistoryRecord, *, limit: int) -> None:
        records = self.load()
        records.insert(0, record)
        trimmed = records[:limit]
        path = history_file_path()
        path.write_text(
            json.dumps([item.to_dict() for item in trimmed], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
