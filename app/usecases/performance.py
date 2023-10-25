from __future__ import annotations

import hashlib
import logging
from typing import TypedDict

import app.state
import config
from app.constants.mode import Mode
from app.objects.path import Path


async def check_local_file(osu_file_path: Path, map_id: int, map_md5: str) -> bool:
    if (
        not osu_file_path.exists()
        or hashlib.md5(osu_file_path.read_bytes()).hexdigest() != map_md5
    ):
        async with app.state.services.http.get(
            f"https://old.ppy.sh/osu/{map_id}",
        ) as response:
            if response.status != 200:
                return False

            osu_file_path.write_bytes(await response.read())

    return True


class PerformanceScore(TypedDict):
    beatmap_id: int
    mode: int
    mods: int
    max_combo: int
    accuracy: float
    miss_count: int


async def calculate_performances(
    scores: list[PerformanceScore],
) -> list[tuple[float, float]]:
    async with app.state.services.http.post(
        f"{config.PERFORMANCE_SERVICE_URL}/api/v1/calculate",
        json=scores,
    ) as resp:
        if resp.status not in range(200, 300):
            logging.error(
                "Performance service returned non-2xx code on calculate_performances",
                extra={"status": resp.status},
            )
            return [(0.0, 0.0)] * len(scores)

        data = await resp.json()
        return [(result["pp"], result["stars"]) for result in data]


# TODO: split sr & pp calculations
async def calculate_performance(
    beatmap_id: int,
    mode: Mode,
    mods: int,
    max_combo: int,
    acc: float,
    nmiss: int,
) -> tuple[float, float]:
    async with app.state.services.http.post(
        f"{config.PERFORMANCE_SERVICE_URL}/api/v1/calculate",
        json=[
            {
                "beatmap_id": beatmap_id,
                "mode": mode.as_vn,
                "mods": mods,
                "max_combo": max_combo,
                "accuracy": acc,
                "miss_count": nmiss,
            },
        ],
    ) as resp:
        if resp.status != 200:
            logging.error(
                "Performance service returned non-2xx code on calculate_performance",
                extra={"status": resp.status},
            )
            return 0.0, 0.0

        data = (await resp.json())[0]
        return data["pp"], data["stars"]
