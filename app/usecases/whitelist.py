from __future__ import annotations

import asyncio

import app.state
import logger
from app.constants.mode import Mode
from config import config

WHITELIST: dict[int, int] = {}
FIVE_MINUTES = 60 * 5

# 0 = none
# 1 = vanilla
# 2 = relax
# 2 = autopilot
# 3 = all


def _match_verified(whitelist_int: int, mode: Mode) -> bool:
    if mode.relax or mode.autopilot:
        return whitelist_int in (2, 3)

    return whitelist_int in (1, 3)


async def get_whitelisted(user_id: int, mode: Mode) -> bool:
    if whitelist_int := WHITELIST.get(user_id):
        return _match_verified(whitelist_int, mode)

    whitelist_int = await app.state.services.database.fetch_val(
        "SELECT whitelist FROM users WHERE id = :uid",
        {"uid": user_id},
    )

    WHITELIST[user_id] = whitelist_int
    return _match_verified(WHITELIST[user_id], mode)


async def load_whitelist() -> None:
    # fetch all to store who don't have verified too
    db_whitelists = await app.state.services.database.fetch_all(
        "SELECT id, whitelist FROM users",
    )

    for db_whitelist in db_whitelists:
        WHITELIST[db_whitelist["id"]] = db_whitelist["whitelist"]

    logger.info(f"Cached whitelist for {len(db_whitelists)} users!")


async def update_whitelist_task() -> None:
    while True:
        await load_whitelist()
        await asyncio.sleep(FIVE_MINUTES)
