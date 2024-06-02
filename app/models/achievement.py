from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.score import Score
    from app.models.stats import Stats


@dataclass
class Achievement:
    id: int
    file: str
    name: str
    desc: str
    cond: Callable[[Score, int, Stats], bool]

    @property
    def full_name(self) -> str:
        return f"{self.file}+{self.name}+{self.desc}"
