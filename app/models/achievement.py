from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class Achievement:
    id: int
    file: str
    name: str
    desc: str
    cond: Callable

    @property
    def full_name(self) -> str:
        return f"{self.file}+{self.name}+{self.desc}"
