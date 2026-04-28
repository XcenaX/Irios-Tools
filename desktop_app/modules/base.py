from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget


@dataclass(frozen=True)
class ModuleDescriptor:
    id: str
    title: str
    summary: str
    category: str
    order: int
    page_factory: Callable[[object], QWidget]
    is_enabled: Callable[[object], bool]
