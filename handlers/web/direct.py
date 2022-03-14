# TODO: Cleanup
from conn.web_client import simple_get_json
from constants.statuses import Status
from helpers.user import safe_name
from logger import error, info
from globals import caches
from config import config
import traceback
from starlette.requests import Request
from starlette.responses import PlainTextResponse, RedirectResponse

# Constants.
PASS_ERR = b"error: pass"
USING_CHIMU_V1 = "https://api.chimu.moe/v1" == config.DIRECT_URL
URI_SEARCH = f"{config.DIRECT_URL}/search"
CHIMU_SPELL = "SetId" if USING_CHIMU_V1 else "SetID"
BASE_HEADER = (
    "{{{ChimuSpell}}}.osz|{{Artist}}|{{Title}}|{{Creator}}|{{RankedStatus}}|10.0|"
    "{{LastUpdate}}|{{{ChimuSpell}}}|0|{{Video}}|0|0|0|"
).format(ChimuSpell=CHIMU_SPELL)
CHILD_HEADER = "[{DiffName} ⭐{DifficultyRating:.2f}] {{CS: {CS} / OD: {OD} / AR: {AR} / HP: {HP}}}@{Mode}"


def _format_search_response(diffs: dict, bmap: dict):
    """Formats the beatmapset dictionary to full direct response."""

    base_str = BASE_HEADER.format(**bmap, Video=int(bmap["HasVideo"]))

    return base_str + ",".join(CHILD_HEADER.format(**diff) for diff in diffs)


async def download_map(req: Request):
    """Handles osu!direct map download route"""

    map_id = req.path_params['map_id']
    domain = config.DIRECT_URL.split("/")[2]
    beatmap_id = int(map_id.removesuffix("n"))
    no_vid = "n" == map_id[-1]

    url = f"https://{domain}/d/{beatmap_id}{'n' if no_vid else ''}"
    if USING_CHIMU_V1:
        url = f"{config.DIRECT_URL}/download/{beatmap_id}?n={int(no_vid)}"
    return RedirectResponse(url, status_code=302)


async def get_set_handler(req: Request) -> None:
    """Handles a osu!direct pop-up link response."""

    nick = req.query_params.get("u", "")
    password = req.query_params.get("h", "")
    user_id = await caches.name.id_from_safe(safe_name(nick))

    # Handle Auth..
    if not await caches.password.check_password(user_id, password) or not nick:
        return PlainTextResponse(PASS_ERR)

    if "b" in req.query_params:
        bmap_id = req.query_params.get("b")

        bmap_resp = await simple_get_json(
            f"{config.DIRECT_URL}/{'map' if USING_CHIMU_V1 else 'b'}/{bmap_id}"
        )
        if not bmap_resp or (USING_CHIMU_V1 and int(bmap_resp.get("code", "404")) != 0):
            return PlainTextResponse()
        bmap_set = (
            bmap_resp["data"]["ParentSetId"]
            if USING_CHIMU_V1
            else bmap_resp["ParentSetID"]
        )

    elif "s" in req.query_params:
        bmap_set = req.query_params.get("s")

    bmap_set_resp = await simple_get_json(
        f"{config.DIRECT_URL}/{'set' if USING_CHIMU_V1 else 's'}/{bmap_set}"
    )
    if not bmap_set_resp or (USING_CHIMU_V1 and int(bmap_resp.get("code", "404")) != 0):
        return PlainTextResponse()

    json_data = bmap_set_resp["data"] if USING_CHIMU_V1 else bmap_set_resp
    return PlainTextResponse(_format_search_response({}, json_data))


async def direct_get_handler(req: Request) -> None:
    """Handles osu!direct panels response."""

    # Get all keys.
    nickname = req.query_params.get("u", "")
    password = req.query_params.get("h", "")
    status = Status.from_direct(int(req.query_params.get("r", "0")))
    query = req.query_params.get("q", "").replace("+", " ")
    offset = int(req.query_params.get("p", "0")) * 100
    mode = int(req.query_params.get("m", "-1"))
    user_id = await caches.name.id_from_safe(safe_name(nickname))

    # Handle Auth..
    if not await caches.password.check_password(user_id, password) or not nickname:
        return PlainTextResponse(PASS_ERR)

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
        error(f"Error with direct search ({URI_SEARCH}): {traceback.format_exc()}")
        return PlainTextResponse("-1\nAn error has occured when fetching direct listing!")

    if not res or (USING_CHIMU_V1 and int(res.get("code", "404")) != 0):
        return PlainTextResponse("0")

    bmaps = res["data"] if USING_CHIMU_V1 else res
    response = [f"{'101' if len(bmaps) == 100 else len(bmaps)}"]
    for bmap in bmaps:
        if "ChildrenBeatmaps" not in bmap:
            continue

        sorted_diffs = sorted(
            bmap["ChildrenBeatmaps"], key=lambda b: b["DifficultyRating"]
        )
        response.append(_format_search_response(sorted_diffs, bmap))

    return PlainTextResponse("\n".join(response))
