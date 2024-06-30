from __future__ import annotations

import logging
from typing import Any

import httpx

import app.state
import config
from app.constants.mode import Mode
from app.constants.ranked_status import RankedStatus
from app.models.beatmap import Beatmap

beatmaps_service_http_client = httpx.AsyncClient(
    base_url=config.BEATMAPS_SERVICE_BASE_URL,
)


def _remap_beatmap_to_score_service_model(beatmap: dict[str, Any]) -> Beatmap:
    return Beatmap(
        md5=beatmap["beatmap_md5"],
        id=beatmap["beatmap_id"],
        set_id=beatmap["beatmapset_id"],
        song_name=beatmap["song_name"],
        status=RankedStatus(beatmap["ranked"]),
        plays=beatmap["playcount"],
        passes=beatmap["passcount"],
        mode=Mode(beatmap["mode"]),
        od=beatmap["od"],
        ar=beatmap["ar"],
        hit_length=beatmap["hit_length"],
        last_update=beatmap["latest_update"],
        max_combo=beatmap["max_combo"],
        bpm=beatmap["bpm"],
        filename=beatmap["file_name"],
        frozen=beatmap["ranked_status_freezed"],
        rankedby=beatmap["rankedby"],
        rating=beatmap["rating"],
        bancho_ranked_status=(
            RankedStatus(beatmap["bancho_ranked_status"])
            if beatmap["bancho_ranked_status"] is not None
            else None
        ),
        count_circles=beatmap["count_circles"],
        count_sliders=beatmap["count_sliders"],
        count_spinners=beatmap["count_spinners"],
    )


async def fetch_by_md5(beatmap_md5: str, /) -> Beatmap | None:
    try:
        response = await beatmaps_service_http_client.get(
            f"/api/akatsuki/v1/beatmaps/lookup",
            params={"beatmap_md5": beatmap_md5},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        response_data = response.json()
        return _remap_beatmap_to_score_service_model(response_data)
    except Exception:
        logging.exception(
            "Failed to fetch beatmap by md5 from beatmaps-service",
            extra={"beatmap_md5": beatmap_md5},
        )
        return None


async def fetch_by_id(beatmap_id: int, /) -> Beatmap | None:
    try:
        response = await beatmaps_service_http_client.get(
            f"/api/akatsuki/v1/beatmaps/lookup",
            params={"beatmap_id": beatmap_id},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        response_data = response.json()
        return _remap_beatmap_to_score_service_model(response_data)
    except Exception:
        logging.exception(
            "Failed to fetch beatmap by id from beatmaps-service",
            extra={"beatmap_id": beatmap_id},
        )
        return None


async def increment_playcount(
    *,
    beatmap: Beatmap,
    increment_passcount: bool,
) -> None:
    # TODO: refactor this to hit an endpoint on beatmaps-service
    beatmap.plays += 1
    if increment_passcount:
        beatmap.passes += 1

    await app.state.services.database.execute(
        "UPDATE beatmaps SET passcount = passcount + :passcount_increment, playcount = playcount + 1 WHERE beatmap_md5 = :md5",
        {"passcount_increment": int(increment_passcount), "md5": beatmap.md5},
    )
