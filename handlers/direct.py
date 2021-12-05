# TODO: Cleanup
import traceback
import requests
from random import randint, shuffle
from lenhttp import Request
from globs import caches
from logger import error, info
from conn.web_client import simple_get_json, simple_get
from consts.statuses import Status
from helpers.user import safe_name
from config import conf

# Constants.
PASS_ERR = b"error: pass"
USING_CHIMU_V1 = "https://api.chimu.moe/v1" == conf.direct_api_url
URI_SEARCH = f"{conf.direct_api_url}/search"
CHIMU_SPELL = "SetId" if USING_CHIMU_V1 else "SetID"
BASE_HEADER = (
    "{{{ChimuSpell}}}.osz|{{Artist}}|{{Title}}|{{Creator}}|{{RankedStatus}}|10.0|"
    "{{LastUpdate}}|{{{ChimuSpell}}}|0|{{Video}}|0|0|0|"
).format(ChimuSpell=CHIMU_SPELL)
CHILD_HEADER = "[{DiffName} ⭐{DifficultyRating:.2f}] {{CS: {CS} / OD: {OD} / AR: {AR} / HP: {HP}}}@{Mode}"


def __format_search_response(diffs: dict, bmap: dict):
    """Formats the beatmapset dictionary to full direct response."""

    base_str = BASE_HEADER.format(**bmap, Video=int(bmap["HasVideo"]))

    return base_str + ",".join(CHILD_HEADER.format(**diff) for diff in diffs)


async def download_map(req: Request, map_id: str):
    """Handles osu!direct map download route"""

    domain = conf.direct_api_url.split("/")[2]
    beatmap_id = int(map_id.removesuffix("n"))
    no_vid = "n" == map_id[-1]

    url = f"https://{domain}/d/{beatmap_id}"
    if USING_CHIMU_V1:
        url = f"{conf.direct_api_url}/download/{beatmap_id}?n={int(no_vid)}"
    req.add_header("Location", url)
    return (302, b"")


async def get_set_handler(req: Request) -> None:
    """Handles a osu!direct pop-up link response."""

    nick = req.get_args.get("u", "")
    password = req.get_args.get("h", "")
    user_id = await caches.name.id_from_safe(safe_name(nick))

    # Handle Auth..
    if not await caches.password.check_password(user_id, password) or not nick:
        return PASS_ERR

    if "b" in req.get_args:
        bmap_id = req.get_args.get("b")

        bmap_resp = await simple_get_json(
            f"{conf.direct_api_url}/{'map' if USING_CHIMU_V1 else 'b'}/{bmap_id}"
        )
        if not bmap_resp or (USING_CHIMU_V1 and int(bmap_resp.get("code", "404")) != 0):
            return b""
        bmap_set = (
            bmap_resp["data"]["ParentSetId"]
            if USING_CHIMU_V1
            else bmap_resp["ParentSetID"]
        )

    elif "s" in req.get_args:
        bmap_set = req.get_args.get("s")

    bmap_set_resp = await simple_get_json(
        f"{conf.direct_api_url}/{'set' if USING_CHIMU_V1 else 's'}/{bmap_set}"
    )
    if not bmap_set_resp or (USING_CHIMU_V1 and int(bmap_resp.get("code", "404")) != 0):
        return b""  # THIS SHOULD NEVER HAPPEN.

    json_data = bmap_set_resp["data"] if USING_CHIMU_V1 else bmap_set_resp
    return __format_search_response({}, json_data).encode()


async def direct_get_handler(req: Request) -> None:
    """Handles osu!direct panels response."""

    # Get all keys.
    nickname = req.get_args.get("u", "")
    password = req.get_args.get("h", "")
    status = Status.from_direct(int(req.get_args.get("r", "0")))
    query = req.get_args.get("q", "").replace("+", " ")
    offset = int(req.get_args.get("p", "0")) * 100
    mode = int(req.get_args.get("m", "-1"))
    user_id = await caches.name.id_from_safe(safe_name(nickname))

    # Handle Auth..
    if not await caches.password.check_password(user_id, password) or not nickname:
        return PASS_ERR

    mirror_params = {"amount": 100, "offset": offset}
    if status is not None:
        mirror_params["status"] = status.to_direct()

    if query not in ("Newest", "Top Rated", "Most Played"):
        mirror_params["query"] = query

    if mode != -1:
        mirror_params["mode"] = mode
    info(f"{nickname} requested osu!direct search with query: {query or 'None'}")

    try:
        res = await simple_get_json(URI_SEARCH, mirror_params)
    except Exception:
        error(f"Error with direct search: {traceback.format_exc()}")
        return b"-1\nError has occured when fetching direct listing!"

    if not res or (USING_CHIMU_V1 and int(res.get("code", "404")) != 0):
        return b"0"

    bmaps = res["data"] if USING_CHIMU_V1 else res
    response = [f"{'101' if len(bmaps) == 100 else len(bmaps)}"]
    for bmap in bmaps:
        if "ChildrenBeatmaps" not in bmap:
            continue

        sorted_diffs = sorted(
            bmap["ChildrenBeatmaps"], key=lambda b: b["DifficultyRating"]
        )
        response.append(__format_search_response(sorted_diffs, bmap))

    return ("\n".join(response)).encode()
