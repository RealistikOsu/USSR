from __future__ import annotations

from datetime import timedelta
from typing import Optional

import app.state
from config import config


async def cache(user_id: int, has_badge: bool) -> None:
    await app.state.services.redis.set(
        f"ussr:verified:{user_id}",
        int(has_badge),
        timedelta(days=1),
    )


async def get_verified_cache(user_id: int) -> Optional[bool]:
    cache_badge = await app.state.services.redis.get(
        f"ussr:verified:{user_id}",
    )

    return cache_badge == "1"


async def get_verified(user_id: int) -> bool:
    cached_badge = await get_verified_cache(user_id)
    if cached_badge is not None:
        return cached_badge

    has_badge = await app.state.services.database.fetch_val(
        "SELECT 1 FROM user_badges WHERE user = :uid AND badge = :bid",
        {"uid": user_id, "bid": config.srv_verified_badge},
    )

    if not has_badge:
        has_badge = False

    await cache(user_id, has_badge)
    return has_badge
