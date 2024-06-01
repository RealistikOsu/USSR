from __future__ import annotations

from enum import IntEnum


class ScoreStatus(IntEnum):
    QUIT = 0
    FAILED = 1
    SUBMITTED = 2
    BEST = 3
