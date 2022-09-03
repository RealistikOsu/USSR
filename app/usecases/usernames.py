from __future__ import annotations

import asyncio

import app.state
import logging

USERNAMES: dict[int, str] = {}
FIVE_MINUTES = 60 * 5


async def get_username(user_id: int) -> str:
    if user_id in USERNAMES:
        return USERNAMES[user_id]

    return await update_username(user_id)


async def update_username(user_id: int) -> str:
    username = await app.state.services.database.fetch_val(
        "SELECT username FROM users WHERE id = :id",
        {"id": user_id},
    )

    if not username:
        USERNAMES[user_id] = ""
        return ""  # xd

    USERNAMES[user_id] = username
    return username


async def load_usernames() -> None:
    db_usernames = await app.state.services.database.fetch_all(
        "SELECT id, username FROM users",
    )

    for db_user in db_usernames:
        USERNAMES[db_user["id"]] = db_user["username"]

    logging.info(f"Cached usernames for {len(db_usernames)} users!")


async def update_usernames_task() -> None:
    while True:
        await load_usernames()
        await asyncio.sleep(FIVE_MINUTES)
