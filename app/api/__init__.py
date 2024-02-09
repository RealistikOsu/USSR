from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Path
from fastapi import Query
from fastapi import Request
from fastapi import Response
from fastapi.responses import ORJSONResponse
from fastapi.responses import RedirectResponse

from . import direct
from . import error
from . import lastfm
from . import leaderboards
from . import pp
from . import rate
from . import replays
from . import score_sub
from . import screenshots
from . import seasonals
from app.models.user import User
from app.usecases.user import authenticate_user
from config import config

router = APIRouter(default_response_class=Response)

router.add_api_route("/web/osu-osz2-getscores.php", leaderboards.get_leaderboard)
router.add_api_route(
    "/web/osu-submit-modular-selector.php",
    score_sub.submit_score,
    methods=["POST"],
)

router.add_api_route(
    "/web/osu-screenshot.php",
    screenshots.upload_screenshot,
    methods=["POST"],
)

router.add_api_route("/web/osu-getreplay.php", replays.get_replay)
router.add_api_route("/web/replays/{score_id}", replays.get_full_replay)

if config.meili_direct:
    router.add_api_route("/web/osu-search.php", direct.osu_direct_meili)
else:
    router.add_api_route("/web/osu-search.php", direct.osu_direct_cheesegull)
router.add_api_route("/web/osu-search-set.php", direct.beatmap_card)
router.add_api_route("/d/{set_id}", direct.download_map)

router.add_api_route("/web/osu-getseasonal.php", seasonals.get_seasonals)

router.add_api_route("/web/lastfm.php", lastfm.lastfm, methods=["POST"])

router.add_api_route(
    "/web/osu-error.php",
    error.error,
    methods=["POST"],
)

router.add_api_route("/web/osu-rate.php", rate.rate_map)

router.add_api_route("/api/v1/pp", pp.calculate_pp)


@router.get("/web/bancho-connect.php")
async def bancho_connect():
    return b""


@router.get("/p/doyoureallywanttoaskpeppy")
async def peppy():
    return b"This is a peppy skill issue, please ignore."


async def osu_redirect(request: Request, _: int = Path(...)):
    return RedirectResponse(
        url=f"https://osu.ppy.sh{request['path']}",
        status_code=301,
    )


for pattern in (
    "/beatmapsets/{_}",
    "/beatmaps/{_}",
    "/community/forums/topics/{_}",
    "/web/maps/{_}",
):
    router.get(pattern)(osu_redirect)


@router.post("/difficulty-rating")
async def difficulty_rating(request: Request):
    return RedirectResponse(
        url=f"https://osu.ppy.sh{request['path']}",
        status_code=307,
    )


@router.get("/web/osu-getfriends.php")
async def get_friends(
    user: User = Depends(authenticate_user(Query, "u", "h")),
):
    return "\n".join(map(str, user.friends))


@router.get("/api/v1/status")
async def status_handler():
    return ORJSONResponse(
        {"status": 200, "server_status": 1},
    )
