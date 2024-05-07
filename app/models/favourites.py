from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserFavourite:
    user_id: int
    beatmapset_id: int
    created_at: datetime
