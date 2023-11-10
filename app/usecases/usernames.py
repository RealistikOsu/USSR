from __future__ import annotations

import app.state


async def get_username(user_id: int) -> str | None:
    username = await app.state.services.database.fetch_val(
        "SELECT username FROM users WHERE id = :id",
        {"id": user_id},
    )
    return username
