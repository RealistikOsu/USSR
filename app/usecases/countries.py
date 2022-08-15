from __future__ import annotations

from datetime import timedelta
from typing import Optional

import app.state


async def cache(user_id: int, country: str) -> None:
    await app.state.services.redis.set(
        f"ussr:countries:{user_id}",
        country,
        timedelta(days=1),
    )


async def get_cache(user_id: int) -> Optional[str]:
    return await app.state.services.redis.get(
        f"ussr:countries:{user_id}",
    )


async def get(user_id: int) -> str:
    cached_country = await get_cache(user_id)
    if cached_country:
        return cached_country

    country = await app.state.services.database.fetch_val(
        "SELECT country FROM users WHERE id = :id",
        {"id": user_id},
    )

    if not country:
        await cache(user_id, "XX")
        return "XX"  # xd

    await cache(user_id, country)
    return country
