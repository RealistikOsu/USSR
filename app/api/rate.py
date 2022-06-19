from __future__ import annotations

from typing import Optional

from fastapi import Depends
from fastapi import Query

import app.state
import app.usecases
import logger
from app.models.beatmap import Beatmap
from app.models.user import User
from app.usecases.user import authenticate_user


async def check_user_rated(user: User, beatmap: Beatmap):
    return await app.state.services.database.fetch_val(
        "SELECT 1 FROM beatmaps_rating WHERE user_id = :uid AND beatmap_md5 = :md5",
        {"uid": user.id, "md5": beatmap.md5},
    )


async def add_rating(user_id: int, map_md5: str, rating: int) -> float:
    await app.state.services.database.execute(
        "INSERT INTO beatmaps_rating (user_id, rating, beatmap_md5) VALUES (:id, :rating, :md5)",
        {"id": user_id, "rating": rating, "md5": map_md5},
    )

    new_rating = await app.state.services.database.fetch_val(
        "SELECT AVG(rating) FROM beatmaps_rating WHERE beatmap_md5 = :md5",
        {"md5": map_md5},
    )

    await app.state.services.database.execute(
        "UPDATE beatmaps SET rating = :rating WHERE beatmap_md5 = :md5",
        {"rating": new_rating, "md5": map_md5},
    )

    return new_rating


async def rate_map(
    user: User = Depends(authenticate_user(Query, "u", "p")),
    map_md5: str = Query(..., alias="c"),
    rating: Optional[int] = Query(None, alias="v", ge=1, le=10),
):
    beatmap = await app.usecases.beatmap.fetch_by_md5(map_md5)
    if not beatmap:
        return b"no exist"

    if not beatmap.has_leaderboard:
        return b"not ranked"

    if await check_user_rated(user, beatmap):
        return f"alreadyvoted\n{beatmap.rating}".encode()

    if rating:
        new_rating = await add_rating(user.id, map_md5, rating)
        beatmap.rating = new_rating

        logger.info(
            f"{user} has rated {beatmap.song_name} with rating {rating} (new average: {new_rating:.2f})",
        )
        return f"alreadyvoting\n{new_rating:.2f}".encode()
    else:
        return b"ok"
