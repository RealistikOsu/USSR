from __future__ import annotations

import asyncio
from typing import Any
from typing import Optional
from urllib.parse import unquote_plus

from fastapi import Depends
from fastapi import Path
from fastapi import Query
from fastapi import status
from fastapi.responses import RedirectResponse

import app.state
import app.usecases
import config
from app.adapters import amplitude
from app.constants.ranked_status import RankedStatus
from app.models.user import User
from app.usecases.user import authenticate_user

USING_CHIMU = "https://api.chimu.moe/v1" == config.DIRECT_URL
USING_KITSU = "https://us.kitsu.moe/api" == config.DIRECT_URL
CHIMU_SET_ID_SPELLING = "SetId" if USING_CHIMU else "SetID"

DIRECT_SET_INFO_FMTSTR = (
    "{{{chimu_set_id_spelling}}}.osz|{{Artist}}|{{Title}}|{{Creator}}|"
    "{{RankedStatus}}|10.0|{{LastUpdate}}|{{{chimu_set_id_spelling}}}|"
    "0|{{HasVideo}}|0|0|0|{{diffs}}"
).format(chimu_set_id_spelling="SetId" if USING_CHIMU else "SetID")

DIRECT_MAP_INFO_FMTSTR = (
    "[{DifficultyRating:.2f}⭐] {DiffName} "
    "{{cs: {CS} / od: {OD} / ar: {AR} / hp: {HP}}}@{Mode}"
)


async def osu_direct(
    user: User = Depends(authenticate_user(Query, "u", "h")),
    ranked_status: int = Query(..., alias="r", ge=0, le=8),
    query: str = Query(..., alias="q"),
    mode: int = Query(..., alias="m", ge=-1, le=3),
    page_num: int = Query(..., alias="p"),
):
    search_url = f"{config.DIRECT_URL}/search"

    params: dict[str, Any] = {"amount": 101, "offset": page_num}

    if "akatsuki.gg" in config.DIRECT_URL or "akatest.space" in config.DIRECT_URL:
        params["osu_direct"] = True

    if unquote_plus(query) not in ("Newest", "Top Rated", "Most Played"):
        params["query"] = query

    if mode != -1:
        params["mode"] = mode

    if ranked_status != 4:
        params["status"] = RankedStatus.from_direct(ranked_status).osu_api

    try:
        response = await app.state.services.http_client.get(
            search_url,
            params=params,
            timeout=5,
        )
        if response.status_code != status.HTTP_200_OK:
            return b"-1\nFailed to retrieve data from the beatmap mirror."

        result = response.json()

        # if USING_KITSU: # kitsu is kinda annoying here and sends status in body
        #    if result["code"] != 200:
        #        return b"-1\nFailed to retrieve data from the beatmap mirror."

    except asyncio.exceptions.TimeoutError:
        return b"-1\n3rd party beatmap mirror we depend on timed out. Their server is likely down."

    result_len = len(result)
    ret = [f"{'101' if result_len == 100 else result_len}"]

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
        asyncio.create_task(
            amplitude.track(
                event_name="osudirect_search",
                user_id=str(user.id),
                device_id=None,
                event_properties={
                    "query": query,
                    "page_num": page_num,
                    "game_mode": (
                        amplitude.format_mode(mode) if mode != -1 else "All modes"
                    ),
                    "ranked_status": ranked_status,
                },
            ),
        )

    return "\n".join(ret).encode()


async def beatmap_card(
    user: User = Depends(authenticate_user(Query, "u", "h")),
    map_set_id: Optional[int] = Query(None, alias="s"),
    map_id: Optional[int] = Query(None, alias="b"),
):
    if map_set_id is None and map_id is not None:
        bmap = await app.usecases.beatmap.fetch_by_id(map_id)
        if bmap is None:
            return

        map_set_id = bmap.set_id

    url = f"{config.DIRECT_URL}/{'set' if USING_CHIMU else 's'}/{map_set_id}"
    response = await app.state.services.http_client.get(url, timeout=5)
    if response.status_code != 200:
        return

    result = response.json()

    json_data = result["data"] if USING_CHIMU else result

    if config.AMPLITUDE_API_KEY:
        asyncio.create_task(
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

    return (
        "{chimu_spell}.osz|{Artist}|{Title}|{Creator}|"
        "{RankedStatus}|10.0|{LastUpdate}|{chimu_spell}|"
        "0|0|0|0|0".format(**json_data, chimu_spell=json_data[CHIMU_SET_ID_SPELLING])
    ).encode()


async def download_map(set_id: str = Path(...)):
    domain = config.DIRECT_URL.split("/")[2]

    return RedirectResponse(
        url=f"https://{domain}/d/{set_id}",
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
    )
