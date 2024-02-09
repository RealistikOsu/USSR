from __future__ import annotations

import asyncio

import app.state
import logger


async def fetch(user_id: int) -> str:
    clan_tag = await app.state.services.database.fetch_val(
        "SELECT tag FROM user_clans LEFT JOIN clans ON user_clans.clan = clans.id WHERE user = :id",
        {"id": user_id},
    )

    if not clan_tag:
        return ""
    return clan_tag
