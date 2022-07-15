from __future__ import annotations

import asyncio

import app.state
import logger
from config import config

VERIFIED: dict[int, bool] = {}
FIVE_MINUTES = 60 * 5


async def get_verified(user_id: int) -> bool:
    if user_id in VERIFIED:
        return VERIFIED[user_id]

    has_badge = await app.state.services.database.fetch_val(
        "SELECT 1 FROM user_badges WHERE user = :uid AND badge = :bid",
        {"uid": user_id, "bid": config.srv_verified_badge},
    )

    if not has_badge:
        has_badge = False

    VERIFIED[user_id] = has_badge
    return VERIFIED[user_id]


async def load_verified() -> None:
    # fetch all to store who don't have verified too
    db_users = await app.state.services.database.fetch_all("SELECT id FROM users")

    db_verified = await app.state.services.database.fetch_all(
        "SELECT user FROM user_badges WHERE badge = :bid",
        {"bid": config.srv_verified_badge},
    )

    verified = [b["user"] for b in db_verified]

    for db_user in db_users:
        result = False
        if db_user["id"] in verified:
            result = True

        VERIFIED[db_user["id"]] = result

    logger.info(f"Cached verified badges for {len(db_users)} users!")


async def update_verified_task() -> None:
    while True:
        await load_verified()
        await asyncio.sleep(FIVE_MINUTES)
