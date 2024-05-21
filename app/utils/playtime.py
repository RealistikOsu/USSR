from __future__ import annotations

from typing import TypedDict

from app.constants.mods import Mods


class TimePlayed(TypedDict):
    seconds_active: float
    seconds_inactive: float


def adjust_duration_for_mods(duration: float, mods: int) -> float:
    if mods & (Mods.DOUBLETIME | Mods.NIGHTCORE):
        duration /= 1.50  # 50% speed increase
    elif mods & Mods.HALFTIME:
        duration /= 0.75  # 25% speed decrease
    return duration


def calculate_time_played(
    *,
    failed: bool,
    score_time: int,
    fail_time: int,
    hit_length: int,
    first_hitobject_offset: int,
    mods: int,
) -> TimePlayed:
    if failed:
        seconds_active = fail_time - first_hitobject_offset
    else:
        seconds_active = hit_length

    seconds_inactive = score_time - seconds_active

    return {
        "seconds_active": adjust_duration_for_mods(seconds_active, mods),
        "seconds_inactive": adjust_duration_for_mods(seconds_inactive, mods),
    }
