from __future__ import annotations

from dataclasses import dataclass

from app.constants.mode import Mode


@dataclass
class Stats:
    user_id: int
    mode: Mode

    ranked_score: int
    total_score: int
    pp: float
    rank: int
    country_rank: int
    accuracy: float
    playcount: int
    playtime: int
    max_combo: int
    total_hits: int
    replays_watched: int

    _required_recalc_pp: float = 0.0
    _cur_bonus_pp: float = 0.0
