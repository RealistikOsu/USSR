from __future__ import annotations

import app.state.services


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
