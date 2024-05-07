from __future__ import annotations

from fastapi import Depends
from fastapi import Query

import app.usecases
from app.models.user import User
from app.usecases.user import authenticate_user


async def add_favourite(
    user: User = Depends(authenticate_user(Query, "u", "h")),
    map_set_id: int = Query(..., alias="a"),
) -> bytes:
    if await app.usecases.favourites.exists(user.id, map_set_id):
        return b"You've already favourited this beatmap!"

    await app.usecases.favourites.add_favourite(
        user_id=user.id,
        beatmapset_id=map_set_id,
    )

    return b"Added favourite!"


async def get_favourites(
    user: User = Depends(authenticate_user(Query, "u", "h")),
) -> bytes:
    favourites = await app.usecases.favourites.fetch_all(user.id)
    return "\n".join(
        [str(favourite.beatmapset_id) for favourite in favourites],
    ).encode()
