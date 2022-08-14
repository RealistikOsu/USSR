from __future__ import annotations

from datetime import timedelta
from typing import Optional

import app.state

CLANS: dict[int, str] = {}
FIVE_MINUTES = 60 * 5


async def cache(user_id: int, clan_tag: str) -> None:
    await app.state.services.redis.set(
        f"ussr:clan_tags:{user_id}",
        clan_tag,
        timedelta(days=1),
    )


async def get_cache(user_id: int) -> Optional[str]:
    return await app.state.services.redis.get(
        f"ussr:clan_tags:{user_id}",
    )


async def get_clan(user_id: int) -> str:
    cached_tag = await get_cache(user_id)
    if cached_tag is not None:
        return cached_tag

    return await update_clan(user_id)


async def update_clan(user_id: int) -> str:
    clan_tag = await app.state.services.database.fetch_val(
        "SELECT tag FROM user_clans LEFT JOIN clans ON user_clans.clan = clans.id WHERE user = :id",
        {"id": user_id},
    )

    if not clan_tag:
        clan_tag = ""

    await cache(user_id, clan_tag)
    return clan_tag
