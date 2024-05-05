from __future__ import annotations

import logging

from fastapi import Depends
from fastapi import Path
from fastapi import Query
from fastapi import Response

import app.state
import app.usecases
import config
from app import job_scheduling
from app.adapters import amplitude
from app.constants.mode import Mode
from app.models.score import Score
from app.models.user import User
from app.usecases.user import authenticate_user


async def get_replay(
    user: User = Depends(authenticate_user(Query, "u", "h")),
    score_id: int = Query(..., alias="c"),
):
    mode_rep = Mode.from_offset(score_id)

    db_score = await app.state.services.database.fetch_one(
        f"SELECT mods, play_mode, userid FROM {mode_rep.scores_table} WHERE id = :id",
        {"id": score_id},
    )

    if not db_score:
        logging.error(f"Requested non-existent replay ID {score_id}")
        return b"error: no"

    mode = Mode.from_lb(db_score["play_mode"], db_score["mods"])

    replay_bytes = await app.usecases.replays.download_replay(score_id)
    if replay_bytes is None:
        logging.error(
            f"Requested replay ID {score_id}, but no file could be found",
        )
        return b""

    if db_score["userid"] != user.id:
        await app.usecases.user.increment_replays_watched(db_score["userid"], mode)

    if config.AMPLITUDE_API_KEY:
        job_scheduling.schedule_job(
            amplitude.track(
                event_name="watched_replay",
                user_id=str(user.id),
                device_id=None,
                event_properties={
                    # TODO: could fetch the whole score here
                    "score_id": score_id,
                    "game_mode": amplitude.format_mode(mode),
                },
            ),
        )

    logging.info(f"Served replay ID {score_id}")
    return Response(content=replay_bytes)


async def get_full_replay(
    score_id: int = Path(...),
):
    mode_rep = Mode.from_offset(score_id)

    db_score = await app.state.services.database.fetch_one(
        f"SELECT * FROM {mode_rep.scores_table} WHERE id = :id",
        {"id": score_id},
    )
    if not db_score:
        return b"Score not found!"

    score = Score.from_mapping(db_score)

    replay = await app.usecases.score.build_full_replay(score)
    if replay is None:
        return b"Replay not found!"

    beatmap = await app.usecases.beatmap.fetch_by_md5(score.map_md5)
    if beatmap is None:
        return b"Beatmap not found!"

    username = await app.usecases.usernames.get_username(score.user_id)
    if username is None:
        return b"User not found!"

    filename = f"{username} - {beatmap.song_name} ({score_id}).osr"

    logging.info(f"Serving compiled replay ID {score_id}")
    return Response(
        content=bytes(replay.buffer),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
