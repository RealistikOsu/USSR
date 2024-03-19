from __future__ import annotations

import app.state.services
from app.constants.privileges import Privileges

async def fetch(user_id: int) -> Privileges:
    db_privilege = await app.state.services.database.fetch_val(
        "SELECT privileges FROM users WHERE id = :id",
        {"id": user_id},
    )

    if not db_privilege:
        return Privileges(2)  # assume restricted? xd

    return Privileges(db_privilege)
