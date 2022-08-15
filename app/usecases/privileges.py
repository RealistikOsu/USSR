from __future__ import annotations

from datetime import timedelta
from typing import Optional

import app.state
from app.constants.privileges import Privileges


async def cache(user_id: int, privileges: Privileges) -> None:
    await app.state.services.redis.set(
        f"ussr:privileges:{user_id}",
        privileges.value,
        timedelta(days=1),
    )


async def get_cache(user_id: int) -> Optional[Privileges]:
    res = await app.state.services.redis.get(
        f"ussr:privileges:{user_id}",
    )
    if res:
        return Privileges(int(res))


async def get(user_id: int) -> Privileges:
    res_db = await get_cache(user_id)
    if res_db:
        return res_db

    return await update_privilege(user_id)


async def update_privilege(user_id: int) -> Privileges:
    db_privilege = await app.state.services.database.fetch_val(
        "SELECT privileges FROM users WHERE id = :id",
        {"id": user_id},
    )

    if not db_privilege:
        db_privilege = 2

    privilege = Privileges(db_privilege)
    await cache(user_id, privilege)

    return privilege
