from __future__ import annotations

from typing import Any
from typing import Mapping

import app.state.services
from app.models.favourites import UserFavourite


READ_PARAMS = """
    user_id,
    beatmapset_id,
    created_at
"""


def serialize(obj: UserFavourite) -> dict[str, Any]:
    return {
        "user_id": obj.user_id,
        "beatmapset_id": obj.beatmapset_id,
        "created_at": obj.created_at,
    }


def deserialize(rec: Mapping[str, Any]) -> UserFavourite:
    return UserFavourite(
        user_id=rec["user_id"],
        beatmapset_id=rec["beatmapset_id"],
        created_at=rec["created_at"],
    )


async def exists(user_id: int, beatmapset_id: int) -> bool:
    rec = await app.state.services.database.fetch_one(
        """\
        SELECT 1
        FROM user_favourites
        WHERE user_id = :user_id
        AND beatmapset_id = :beatmapset_id
        """,
        {"user_id": user_id, "beatmapset_id": beatmapset_id},
    )
    return rec is not None


async def add_favourite(user_id: int, beatmapset_id: int) -> None:
    await app.state.services.database.execute(
        """\
        INSERT INTO user_favourites (user_id, beatmapset_id)
        VALUES (:user_id, :beatmapset_id)
        """,
        {"user_id": user_id, "beatmapset_id": beatmapset_id},
    )


async def fetch_all(user_id: int) -> list[UserFavourite]:
    recs = await app.state.services.database.fetch_all(
        f"""\
        SELECT {READ_PARAMS}
        FROM user_favourites
        WHERE user_id = :user_id
        """,
        {"user_id": user_id},
    )
    return [deserialize(rec) for rec in recs]
