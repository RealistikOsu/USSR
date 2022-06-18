# Replay related handlers.
from __future__ import annotations

from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.responses import Response

from constants.c_modes import CustomModes
from constants.modes import Mode
from globals.connections import sql
from helpers.replays import build_full_replay
from helpers.replays import read_replay
from helpers.user import incr_replays_watched
from logger import error
from logger import info
from objects.score import Score

BASE_QUERY = "SELECT play_mode, userid FROM {} WHERE id = %s LIMIT 1"
ERR_NOT_FOUND = "error: no"


async def get_replay_web_handler(req: Request) -> Response:
    """Handles the in-game replay downloads, incrementing replays watched
    appropeately.
    URL: `/web/osu-getreplay.php`
    """

    # Grab our data. TODO: Maybe auth?
    score_id = int(req.query_params["c"])
    c_mode = CustomModes.from_score_id(score_id)

    score_data_db = await sql.fetchone(BASE_QUERY.format(c_mode.db_table), (score_id,))

    # Handle replay not found.
    if not score_data_db:
        error(f"Requested non-existent replay score {score_id}")
        return PlainTextResponse(ERR_NOT_FOUND)

    _play_mode, user_id = score_data_db
    mode = Mode(_play_mode)

    rp = await read_replay(score_id, c_mode)
    if not rp:
        error(f"Requested non-existent replay file {score_id}.osr")
        return PlainTextResponse(ERR_NOT_FOUND)

    # Increment their stats.
    await incr_replays_watched(user_id, mode)

    info(f"Successfully served replay {score_id}.osr")
    return Response(rp)


async def get_full_replay_handler(req: Request) -> Response:
    """Retuns a fully built replay with headers. Used for web."""

    score_id = req.path_params["score_id"]
    c_mode = CustomModes.from_score_id(score_id)
    score = await Score.from_db(score_id, c_mode)
    if not score:
        return PlainTextResponse("Score not found!", status_code=404)

    rp = await build_full_replay(score)
    if not rp:
        return PlainTextResponse("Replay not found!", status_code=404)

    filename = f"{score.username} - {score.bmap.song_name} ({score.id}).osr"

    info(f"Served compiled replay {score_id}!")

    return Response(
        bytes(rp.buffer),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
