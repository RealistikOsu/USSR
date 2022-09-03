from __future__ import annotations

import asyncio

import app.state
import logging
from app.constants.privileges import Privileges

PRIVILEGES: dict[int, Privileges] = {}
FIVE_MINUTES = 60 * 5


async def get_privileges(user_id: int) -> Privileges:
    if privileges := PRIVILEGES.get(user_id):
        return privileges

    privileges = await _get_privileges(user_id)
    PRIVILEGES[user_id] = privileges
    return privileges


async def _get_privileges(user_id: int) -> Privileges:
    db_privileges = await app.state.services.database.fetch_val(
        "SELECT privileges FROM users WHERE id = :id",
        {"id": user_id},
    )

    if db_privileges is None:
        raise Exception(f"User {user_id} not found in database!")

    return Privileges(db_privileges)


async def load_privileges() -> None:
    db_privileges = await app.state.services.database.fetch_all(
        "SELECT id, privileges FROM users",
    )

    for db_user in db_privileges:
        PRIVILEGES[db_user["id"]] = Privileges(db_user["privileges"])

    logging.info(f"Cached privileges for {len(db_privileges)} users!")


async def update_privileges_task() -> None:
    while True:
        await load_privileges()
        await asyncio.sleep(FIVE_MINUTES)
