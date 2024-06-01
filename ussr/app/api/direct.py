from __future__ import annotations

import re
from typing import Any
from typing import Optional
from urllib.parse import unquote_plus

import app.state.services
import app.usecases.beatmap
import settings
from app.constants.ranked_status import RankedStatus
from app.models.user import User
from app.usecases.user import authenticate_user
from fastapi import Depends
from fastapi import Path
from fastapi import Query
from fastapi import status
from fastapi.responses import RedirectResponse

USING_CHIMU = "https://api.chimu.moe/v1" == settings.DIRECT_URL
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

DIRECT_MAP_INFO_FMTSTR_MEILI = "{difficulty} od: {od} / ar: {ar}@{mode}"

DIRECT_SET_INFO_FMTSTR_MEILI = (
    "{chimu_spell}.osz|{Artist}|{Title}|{Creator}|"
    "{RankedStatus}|{Rating}|0|{chimu_spell}|"
    "0|0|0|0|0|{diffs}"
)


async def osu_direct_meili(
    user: User = Depends(authenticate_user(Query, "u", "h")),
    ranked_status: int = Query(..., alias="r", ge=0, le=8),
    query: str = Query(..., alias="q"),
    mode: int = Query(..., alias="m", ge=-1, le=3),
    page_num: int = Query(..., alias="p"),
):
    # Special filters
    order = "play_count:desc"
    if query == "Top Rated":
        order = "avg_rating:desc"
        query = ""
    elif query == "Newest":
        order = "id:desc"
        query = ""
    elif query == "Newest":
        query = ""

    filters = []

    if ranked_status != 4:
        status = RankedStatus.from_direct(ranked_status)
        filters.append(f"status={status.value}")

    if mode != -1:
        filters.append(f"modes={mode}")

    index = app.state.services.meili.index("beatmaps")
    search_res = await index.search(
        query,
        offset=page_num * 100,
        limit=100,
        filter=filters,
        sort=[order],
    )

    # Response building
    res = [str(search_res.estimated_total_hits)]

    for beatmap_set in search_res.hits:
        diff_str = ",".join(
            DIRECT_MAP_INFO_FMTSTR_MEILI.format(
                difficulty=child["difficulty"],
                od=child["od"],
                ar=child["ar"],
                mode=child["mode"],
            )
            for child in beatmap_set["children"]
        )
        res.append(
            DIRECT_SET_INFO_FMTSTR_MEILI.format(
                chimu_spell=beatmap_set["id"],
                Artist=beatmap_set["artist"].replace("|", ""),
                Title=beatmap_set["title"].replace("|", ""),
                Creator=beatmap_set["creator"],
                RankedStatus=RankedStatus(beatmap_set["status"]).osu_direct,
                Rating=beatmap_set["avg_rating"],
                diffs=diff_str,
            ),
        )

    return "\n".join(res).encode()


async def osu_direct_cheesegull(
    user: User = Depends(authenticate_user(Query, "u", "h")),
    ranked_status: int = Query(..., alias="r", ge=0, le=8),
    query: str = Query(..., alias="q"),
    mode: int = Query(..., alias="m", ge=-1, le=3),
    page_num: int = Query(..., alias="p"),
):
    search_url = f"{settings.DIRECT_URL}/search"

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

        # Apparently beatmap names can contain the | character. Remove it as it
        # messes up the format. TODO: Look if I can urlencode it instead.
        bmap["Title"] = bmap["Title"].replace("|", "")
        bmap["Artist"] = bmap["Artist"].replace("|", "")
        bmap["Creator"] = bmap["Creator"].replace("|", "")

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

    url = f"{settings.DIRECT_URL}/{'set' if USING_CHIMU else 's'}/{map_set_id}"
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
    domain = settings.DIRECT_URL.split("/")[2]

    return RedirectResponse(
        url=f"https://{domain}/d/{set_id}",
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
    )
