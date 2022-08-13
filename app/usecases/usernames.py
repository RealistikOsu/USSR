from __future__ import annotations

from datetime import timedelta
from typing import Optional

import app.state


async def cache(user_id: int, name: str) -> None:
    await app.state.services.redis.set(
        f"ussr:usernames:{user_id}",
        name,
        timedelta(days=1),
    )


async def get_cache(user_id: int) -> Optional[str]:
    return await app.state.services.redis.get(
        f"ussr:usernames:{user_id}",
    )


async def get_username(user_id: int) -> str:
    redis_name = await get_cache(user_id)
    if redis_name:
        return redis_name

    return await update_username(user_id)


async def update_username(user_id: int) -> str:
    username = await app.state.services.database.fetch_val(
        "SELECT username FROM users WHERE id = :id",
        {"id": user_id},
    )

    if not username:
        username = ""
        return ""  # xd

    await cache(user_id, username)
    return username
