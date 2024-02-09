from __future__ import annotations

import asyncio

from fastapi import Path
from fastapi import Query
from fastapi import Response
from fastapi.responses import FileResponse

import app.state
import app.usecases
import app.utils
import logger
from app.constants.mode import Mode
from app.models.score import Score
from config import config

async def get_replay(
    score_id: int = Query(..., alias="c"),
):
    mode_rep = Mode.from_offset(score_id)

    db_score = await app.state.services.database.fetch_one(
        f"SELECT mods, play_mode, userid FROM {mode_rep.scores_table} WHERE id = :id",
        {"id": score_id},
    )

    if not db_score:
        logger.error(f"Requested non-existent replay ID {score_id}")
        return b"error: no"

    mode = Mode.from_lb(db_score["play_mode"], db_score["mods"])
    replay_bytes = await app.state.services.replay_storage.load(f"replay_{score_id}.osr")
    
    if not replay_bytes:
        logger.error(f"Requested replay ID {score_id}, but no file could be found.")
        return b"error: no"

    asyncio.create_task(
        app.usecases.user.increment_replays_watched(db_score["userid"], mode),
    )

    logger.info(f"Served replay ID {score_id}")
    return Response(content=replay_bytes)


def _make_not_found_resp(text: str) -> Response:
    return Response(
        content=text,
        media_type="text/plain",
        status_code=404,
    )


async def get_full_replay(
    score_id: int = Path(...),
):
    mode_rep = Mode.from_offset(score_id)

    db_score = await app.state.services.database.fetch_one(
        f"SELECT * FROM {mode_rep.scores_table} WHERE id = :id",
        {"id": score_id},
    )
    if not db_score:
        return _make_not_found_resp("Score not found!")

    score = Score.from_dict(db_score)

    replay = await app.usecases.score.build_full_replay(score)
    if not replay:
        return _make_not_found_resp("Replay not found!")

    beatmap = await app.usecases.beatmap.fetch_by_md5(score.map_md5)
    if not beatmap:
        return _make_not_found_resp("Beatmap not found!")

    username = await app.usecases.usernames.get_username(score.user_id)
    if not username:
        return _make_not_found_resp("User not found!")

    filename = f"{username} - {beatmap.song_name} ({score_id}).osr"

    logger.info(f"Serving compiled replay ID {score_id}")
    return Response(
        content=bytes(replay.buffer),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
