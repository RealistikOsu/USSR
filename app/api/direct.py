from __future__ import annotations

import logging
import urllib.parse
from typing import Any

import httpx
from fastapi import Depends
from fastapi import Path
from fastapi import Query
from fastapi import Response
from fastapi import status
from fastapi.responses import RedirectResponse

import app.state
import app.usecases
import config
from app import job_scheduling
from app.adapters import amplitude
from app.constants.ranked_status import RankedStatus
from app.models.user import User
from app.usecases.user import authenticate_user

DIRECT_SET_INFO_FMTSTR = (
    "{SetID}.osz|{Artist}|{Title}|{Creator}|"
    "{RankedStatus}|10.0|{LastUpdate}|{SetID}|"
    "0|{HasVideo}|0|0|0|{diffs}"
)

DIRECT_MAP_INFO_FMTSTR = (
    "[{DifficultyRating:.2f}⭐] {DiffName} "
    "{{cs: {CS} / od: {OD} / ar: {AR} / hp: {HP}}}@{Mode}"
)


async def osu_direct(
    user: User = Depends(authenticate_user(Query, "u", "h")),
    ranked_status: int = Query(..., alias="r", ge=0, le=8),
    query: str = Query(..., alias="q"),
    mode: int = Query(..., alias="m", ge=-1, le=3),
    page: int = Query(..., alias="p"),
) -> Response:
    search_url = f"{config.BEATMAPS_SERVICE_BASE_URL}/public/api/search"

    page_size = 100
    page = page + 1  # the osu! client starts from page 0
    params: dict[str, Any] = {
        "amount": page_size,
        "offset": page * page_size - 1,
    }

    if urllib.parse.unquote_plus(query) not in ("Newest", "Top Rated", "Most Played"):
        params["query"] = query

    if mode != -1:
        params["mode"] = mode

    if ranked_status != 4:
        params["status"] = RankedStatus.from_direct(ranked_status).osu_api

    try:
        response = await app.state.services.http_client.get(
            search_url,
            params=params,
            timeout=15,
        )
        if response.status_code == status.HTTP_404_NOT_FOUND:
            return Response(b"-1\nFailed to retrieve data from the beatmap mirror.")
        response.raise_for_status()
    except Exception:
        logging.exception(
            "Failed to search for results from the beatmap mirror",
            extra={
                "query": query,
                "page": page,
                "page_size": page_size,
                "game_mode": mode,
                "ranked_status": ranked_status,
                "url": search_url,
                "user_id": user.id,
            },
        )
        return Response(b"-1\nFailed to retrieve data from the beatmap mirror.")

    result = response.json()

    # if USING_KITSU: # kitsu is kinda annoying here and sends status in body
    #    if result["code"] != 200:
    #        return b"-1\nFailed to retrieve data from the beatmap mirror."

    # NOTE: 101 informs the osu! client that there are more available
    ret = ["101" if len(result) == 100 else str(len(result))]

    for bmap in result:
        if not bmap["ChildrenBeatmaps"]:
            continue

        diff_sorted_maps = sorted(
            bmap["ChildrenBeatmaps"],
            key=lambda x: x["DifficultyRating"],
        )

        diffs_str = ",".join(
            DIRECT_MAP_INFO_FMTSTR.format(**bm) for bm in diff_sorted_maps
        )
        ret.append(
            DIRECT_SET_INFO_FMTSTR.format(
                **bmap,
                diffs=diffs_str,
            ),
        )

    if config.AMPLITUDE_API_KEY:
        job_scheduling.schedule_job(
            amplitude.track(
                event_name="osudirect_search",
                user_id=str(user.id),
                device_id=None,
                event_properties={
                    "query": query,
                    "page_num": page,
                    "game_mode": (
                        amplitude.format_mode(mode) if mode != -1 else "All modes"
                    ),
                    "ranked_status": ranked_status,
                },
            ),
        )

    return Response("\n".join(ret).encode())


async def beatmap_card(
    user: User = Depends(authenticate_user(Query, "u", "h")),
    map_set_id: int | None = Query(None, alias="s"),
    map_id: int | None = Query(None, alias="b"),
) -> Response:
    if not (map_set_id or map_id):
        logging.warning(
            "No map_set_id or map_id provided to osu-search-set.php API",
            extra={"user_id": user.id},
        )
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    if map_set_id is None and map_id is not None:
        bmap = await app.usecases.akatsuki_beatmaps.fetch_by_id(map_id)
        if bmap is None:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

        map_set_id = bmap.set_id

    url = f"{config.BEATMAPS_SERVICE_BASE_URL}/public/api/s/{map_set_id}"
    try:
        response = await app.state.services.http_client.get(url, timeout=15)
        if response.status_code == status.HTTP_404_NOT_FOUND:
            return Response(status_code=status.HTTP_404_NOT_FOUND)
        response.raise_for_status()
    except Exception:
        logging.exception(
            "Failed to retrieve data from the beatmap mirror",
            extra={
                "beatmapset_id": map_set_id,
                "beatmap_id": map_id,
                "url": url,
                "user_id": user.id,
            },
        )
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    json_data = response.json()

    if config.AMPLITUDE_API_KEY:
        job_scheduling.schedule_job(
            amplitude.track(
                event_name="osudirect_card_view",
                user_id=str(user.id),
                device_id=None,
                event_properties={
                    "beatmapset_id": map_set_id,
                    "beatmap_id": map_id,
                },
            ),
        )

    return Response(
        (
            "{SetID}.osz|{Artist}|{Title}|{Creator}|"
            "{RankedStatus}|10.0|{LastUpdate}|{SetID}|"
            "0|0|0|0|0".format(**json_data)
        ).encode(),
    )


async def download_map(set_id: str = Path(...)) -> Response:
    return RedirectResponse(
        url=f"https://beatmaps.akatsuki.gg/api/d/{set_id}",
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
    )
