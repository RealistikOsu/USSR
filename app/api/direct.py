from __future__ import annotations

import re
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
from app.constants.ranked_status import RankedStatus
from app.models.user import User
from app.usecases.user import authenticate_user
from config import config

USING_CHIMU = "https://api.chimu.moe/v1" == config.direct_url
CHIMU_SPELL = "SetId" if USING_CHIMU else "SetID"

DIRECT_SET_INFO_FMTSTR = (
    "{chimu_spell}.osz|{Artist}|{Title}|{Creator}|"
    "{RankedStatus}|10.0|{LastUpdate}|{chimu_spell}|"
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
    page_num: int = Query(..., alias="p"),
):
    search_url = f"{config.direct_url}/search"

    params: dict[str, Any] = {"amount": 101, "offset": page_num}

    if unquote_plus(query) not in ("Newest", "Top Rated", "Most Played"):
        params["query"] = query

    if mode != -1:
        params["mode"] = mode

    if ranked_status != 4:
        params["status"] = RankedStatus.from_direct(ranked_status).osu_api

    async with app.state.services.http.get(search_url, params=params) as response:
        if response.status != status.HTTP_200_OK:
            return b"-1\nFailed to retrieve data from the beatmap mirror."

        result = await response.json()

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
                chimu_spell=bmap[CHIMU_SPELL],
            ),
        )

    return "\n".join(ret).encode()


async def beatmap_card(
    user: User = Depends(authenticate_user(Query, "u", "h")),
    map_set_id: Optional[int] = Query(None, alias="s"),
    map_id: Optional[int] = Query(None, alias="b"),
):
    if not map_set_id:
        bmap = await app.usecases.beatmap.fetch_by_id(map_id)
        if not bmap:
            return

        map_set_id = bmap.set_id

    url = f"{config.direct_url}/{'set' if USING_CHIMU else 's'}/{map_set_id}"
    async with app.state.services.http.get(url) as response:
        if not response or response.status != 200:
            return

        result = await response.json()

    json_data = result["data"] if USING_CHIMU else result

    return (
        "{chimu_spell}.osz|{Artist}|{Title}|{Creator}|"
        "{RankedStatus}|10.0|{LastUpdate}|{chimu_spell}|"
        "0|0|0|0|0".format(**json_data, chimu_spell=json_data[CHIMU_SPELL])
    ).encode()


async def download_map(set_id: str = Path(...)):
    domain = config.direct_url.split("/")[2]

    return RedirectResponse(
        url=f"https://{domain}/d/{set_id}",
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
    )
