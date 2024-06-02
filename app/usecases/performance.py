from __future__ import annotations

import hashlib
import logging
from typing import TypedDict

import app.state
import config
from app.constants.mode import Mode
from app.objects.path import Path


class PerformanceScore(TypedDict):
    beatmap_id: int
    beatmap_md5: str
    mode: int
    mods: int
    max_combo: int
    accuracy: float
    miss_count: int


async def calculate_performances(
    scores: list[PerformanceScore],
) -> list[tuple[float, float]]:
    response = await app.state.services.http_client.post(
        f"{config.PERFORMANCE_SERVICE_URL}/api/v1/calculate",
        json=scores,
    )
    if not response.is_success:
        logging.error(
            "Performance service returned non-2xx code on calculate_performances",
            extra={"status": response.status_code},
        )
        return [(0.0, 0.0)] * len(scores)

    data = response.json()
    return [(result["pp"], result["stars"]) for result in data]


# TODO: split sr & pp calculations
async def calculate_performance(
    *,
    beatmap_id: int,
    beatmap_md5: str,
    mode: Mode,
    mods: int,
    max_combo: int,
    accuracy: float,
    miss_count: int,
) -> tuple[float, float]:
    response = await app.state.services.http_client.post(
        f"{config.PERFORMANCE_SERVICE_URL}/api/v1/calculate",
        json=[
            {
                "beatmap_id": beatmap_id,
                "beatmap_md5": beatmap_md5,
                "mode": mode.as_vn,
                "mods": mods,
                "max_combo": max_combo,
                "accuracy": accuracy,
                "miss_count": miss_count,
            },
        ],
    )
    if response.status_code != 200:
        logging.error(
            "Performance service returned non-2xx code on calculate_performance",
            extra={"status": response.status_code},
        )
        return 0.0, 0.0

    data = response.json()[0]
    return data["pp"], data["stars"]
