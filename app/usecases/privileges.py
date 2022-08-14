from __future__ import annotations

from datetime import timedelta

import app.state
import logger
from app.constants.privileges import Privileges


async def cache(user_id: int, privileges: Privileges) -> None:
    await app.state.services.redis.set(
        f"ussr:privileges:{user_id}",
        privileges.value,
        timedelta(days=1),
    )


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
