from __future__ import annotations

import asyncio

from fastapi import Path
from fastapi import Query
from fastapi import Response

import app.state
import app.usecases
import app.utils
import logging
from app.constants.mode import Mode
from app.models.score import Score


async def get_replay(
    score_id: int = Query(..., alias="c"),
):
    mode_rep = Mode.from_offset(score_id)

    db_score = await app.state.services.read_database.fetch_one(
        f"SELECT mods, play_mode, userid FROM {mode_rep.scores_table} WHERE id = :id",
        {"id": score_id},
    )

    if not db_score:
        logging.error(f"Requested non-existent replay ID {score_id}")
        return b"error: no"

    mode = Mode.from_lb(db_score["play_mode"], db_score["mods"])

    async with app.state.services.http.get(
        f"http://localhost:3030/get?id={score_id}",
    ) as session:
        if not session or session.status != 200:
            logging.error(
                f"Requested replay ID {score_id}, but no file could be found",
            )
            return b""

        replay_data = await session.read()

    asyncio.create_task(
        app.usecases.user.increment_replays_watched(db_score["userid"], mode),
    )

    logging.info(f"Served replay ID {score_id}")
    return Response(content=replay_data)


async def get_full_replay(
    score_id: int = Path(...),
):
    mode_rep = Mode.from_offset(score_id)

    db_score = await app.state.services.read_database.fetch_one(
        f"SELECT * FROM {mode_rep.scores_table} WHERE id = :id",
        {"id": score_id},
    )
    if not db_score:
        return b"Score not found!"

    score = Score.from_mapping(db_score)

    replay = await app.usecases.score.build_full_replay(score)
    if not replay:
        return b"Replay not found!"

    beatmap = await app.usecases.beatmap.fetch_by_md5(score.map_md5)
    if not beatmap:
        return b"Beatmap not found!"

    username = await app.usecases.usernames.get_username(score.user_id)
    if not username:
        return b"User not found!"

    asyncio.create_task(
        app.usecases.user.increment_replays_watched(db_score["userid"], score.mode),
    )

    filename = f"{username} - {beatmap.song_name} ({score_id}).osr"

    logging.info(f"Serving compiled replay ID {score_id}")
    return Response(
        content=bytes(replay.buffer),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
