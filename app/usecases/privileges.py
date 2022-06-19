from __future__ import annotations

import asyncio

import app.state
import logger
from app.constants.privileges import Privileges

PRIVILEGES: dict[int, Privileges] = {}
FIVE_MINUTES = 60 * 5


async def get_privilege(user_id: int) -> Privileges:
    if user_id in PRIVILEGES:
        return PRIVILEGES[user_id]

    return await update_privilege(user_id)


async def update_privilege(user_id: int) -> Privileges:
    db_privilege = await app.state.services.database.fetch_val(
        "SELECT privileges FROM users WHERE id = :id",
        {"id": user_id},
    )

    if not db_privilege:
        PRIVILEGES[user_id] = Privileges(2)
        return Privileges(2)  # assume restricted? xd

    privilege = Privileges(db_privilege)
    PRIVILEGES[user_id] = privilege

    return privilege


def set_privilege(user_id: int, privileges: Privileges) -> None:
    PRIVILEGES[user_id] = privileges


async def load_privileges() -> None:
    db_privileges = await app.state.services.database.fetch_all(
        "SELECT id, privileges FROM users",
    )

    for db_user in db_privileges:
        PRIVILEGES[db_user["id"]] = Privileges(db_user["privileges"])

    logger.info(f"Cached privileges for {len(db_privileges)} users!")


async def update_privileges_task() -> None:
    while True:
        await load_privileges()
        await asyncio.sleep(FIVE_MINUTES)
