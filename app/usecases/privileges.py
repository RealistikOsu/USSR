from __future__ import annotations

import app.state
from app.constants.privileges import Privileges


async def get_privileges(user_id: int) -> Privileges:
    db_privileges = await app.state.services.database.fetch_val(
        "SELECT privileges FROM users WHERE id = :id",
        {"id": user_id},
    )

    if db_privileges is None:
        raise Exception(f"User {user_id} not found in database!")

    return Privileges(db_privileges)
