from __future__ import annotations

import asyncio

import app.state
import logger

CLANS: dict[int, str] = {}
FIVE_MINUTES = 60 * 5


async def get_clan(user_id: int) -> str:
    if user_id in CLANS:
        return CLANS[user_id]

    clan_tag = await app.state.services.database.fetch_val(
        "SELECT tag FROM user_clans LEFT JOIN clans ON user_clans.clan = clans.id WHERE user = :id",
        {"id": user_id},
    )

    if not clan_tag:
        CLANS[user_id] = ""
        return ""

    CLANS[user_id] = clan_tag
    return clan_tag


async def load_clans() -> None:
    db_usernames = await app.state.services.database.fetch_all(
        "SELECT user, tag FROM user_clans LEFT JOIN clans ON user_clans.clan = clans.id",
    )

    for db_user in db_usernames:
        CLANS[db_user["user"]] = db_user["tag"]

    logger.info(f"Cached clan tags for {len(db_usernames)} users!")


async def update_clans_task() -> None:
    while True:
        await load_clans()
        await asyncio.sleep(FIVE_MINUTES)
