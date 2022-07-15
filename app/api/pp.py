from __future__ import annotations

from typing import Optional

from fastapi import Query
from fastapi.responses import ORJSONResponse

import app.usecases
import logger
from app.constants.mode import Mode
from app.constants.mods import Mods
from app.objects.path import Path
from config import config

TILLERINO_PERCENTAGES = (100, 99, 98, 95)

MAPS_PATH = Path(config.data_dir) / "maps"


async def calculate_pp(
    beatmap_id: int = Query(..., alias="b"),
    mods_arg: Optional[int] = Query(0, alias="m"),
    mode_arg: Optional[int] = Query(0, alias="g", ge=0, le=3),
    acc: Optional[float] = Query(None, alias="a"),
    combo: Optional[int] = Query(0, alias="max_combo"),
):
    mods = Mods(mods_arg)
    mode = Mode.from_lb(mode_arg, mods_arg)

    do_tillerino = acc is None

    beatmap = await app.usecases.beatmap.fetch_by_id(beatmap_id)
    if not beatmap:
        return ORJSONResponse(
            {"status": 400, "message": "Invalid/non-existent beatmap id."},
            400,
        )

    combo = combo if combo else beatmap.max_combo

    file_path = MAPS_PATH / f"{beatmap.id}.osu"
    if not await app.usecases.performance.check_local_file(
        file_path,
        beatmap.id,
        beatmap.md5,
    ):
        return ORJSONResponse(
            {"status": 400, "message": "Invalid/non-existent beatmap id."},
            400,
        )

    star_rating = pp_result = 0.0
    if not do_tillerino:
        pp_result, star_rating = app.usecases.performance.calculate_performance(
            mode,
            mods,
            combo,
            0,  # score
            acc,
            0,  # miss count
            file_path,
        )
    else:
        pp_result = []

        for accuracy in TILLERINO_PERCENTAGES:
            _pp_result, star_rating = app.usecases.performance.calculate_performance(
                mode,
                mods,
                combo,
                0,  # score
                accuracy,
                0,  # misscount
                file_path,
            )

            pp_result.append(_pp_result)

    logger.info(f"Handled PP calculation API request for {beatmap.song_name}!")

    return ORJSONResponse(
        {
            "status": 200,
            "message": "ok",
            "song_name": beatmap.song_name,
            "pp": pp_result,
            "length": beatmap.hit_length,
            "stars": star_rating,
            "ar": beatmap.ar,
            "bpm": beatmap.bpm,
        },
    )
