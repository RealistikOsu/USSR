from __future__ import annotations

import logging
from typing import Optional

from fastapi import Query
from fastapi import status
from fastapi.responses import ORJSONResponse

import app.usecases
from app.adapters import s3
from app.constants.mode import Mode
from app.constants.mods import Mods
from app.usecases.performance import PerformanceScore

COMMON_PP_PERCENTAGES = (
    100.0,
    99.0,
    98.0,
    95.0,
)


async def calculate_pp(
    beatmap_id: int = Query(..., alias="b"),
    mods_arg: int = Query(0, alias="m"),
    mode_arg: int = Query(0, alias="g", ge=0, le=3),
    acc: Optional[float] = Query(None, alias="a"),
    combo: int = Query(0, alias="max_combo"),
):
    mods = Mods(mods_arg)
    mode = Mode.from_lb(mode_arg, mods_arg)

    use_common_pp_percentages = acc is None

    beatmap = await app.usecases.beatmap.id_from_api(beatmap_id, should_save=False)
    if not beatmap:
        return ORJSONResponse(
            content={"message": "Invalid/non-existent beatmap id."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    combo = combo if combo else beatmap.max_combo

    beatmap_exists = (
        # TODO: s3.exists using HEAD request?
        # though, do we even need to do this?
        await s3.download(f"{beatmap.id}.osu", folder=f"beatmaps")
    ) is not None
    if beatmap_exists is None:
        return ORJSONResponse(
            content={"message": "Invalid/non-existent beatmap id."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    star_rating = pp_result = 0.0
    if use_common_pp_percentages:
        pp_requests: list[PerformanceScore] = [
            {
                "beatmap_id": beatmap.id,
                "mode": mode.as_vn,
                "mods": mods,
                "max_combo": combo,
                "accuracy": accuracy,
                "miss_count": 0,
            }
            for accuracy in COMMON_PP_PERCENTAGES
        ]

        pp_result = [
            pp
            for pp, _ in await app.usecases.performance.calculate_performances(
                pp_requests,
            )
        ]
    else:
        pp_result, star_rating = await app.usecases.performance.calculate_performance(
            beatmap.id,
            mode,
            mods,
            combo,
            acc,
            0,  # miss count
        )

    logging.info(f"Handled PP calculation API request for {beatmap.song_name}!")

    return ORJSONResponse(
        {
            "status": 200,
            "message": "ok",
            "song_name": beatmap.song_name,
            "pp": pp_result,
            "length": beatmap.hit_length,
            "stars": star_rating,  # TODO is this wrong for common values?
            "ar": beatmap.ar,
            "bpm": beatmap.bpm,
        },
    )
