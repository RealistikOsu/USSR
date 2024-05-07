from __future__ import annotations

from fastapi import Depends
from fastapi import Query

import app.usecases
import config
from app import job_scheduling
from app.adapters import amplitude
from app.models.user import User
from app.usecases.user import authenticate_user


async def add_favourite(
    user: User = Depends(authenticate_user(Query, "u", "h")),
    beatmapset_id: int = Query(..., alias="a"),
) -> bytes:
    if await app.usecases.favourites.exists(user.id, beatmapset_id):
        return b"You've already favourited this beatmap!"

    await app.usecases.favourites.add_favourite(
        user_id=user.id,
        beatmapset_id=beatmapset_id,
    )

    if config.AMPLITUDE_API_KEY:
        job_scheduling.schedule_job(
            amplitude.track(
                event_name="add_favourite",
                user_id=str(user.id),
                event_properties={"beatmapset_id": beatmapset_id},
            ),
        )

    return b"Added favourite!"


async def get_favourites(
    user: User = Depends(authenticate_user(Query, "u", "h")),
) -> bytes:
    favourites = await app.usecases.favourites.fetch_all(user.id)
    return "\n".join(
        [str(favourite.beatmapset_id) for favourite in favourites],
    ).encode()
