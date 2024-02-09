from __future__ import annotations

import app.state


async def fetch(user_id: int) -> str:
    username = await app.state.services.database.fetch_val(
        "SELECT username FROM users WHERE id = :id",
        {"id": user_id},
    )

    if not username:
        return ""  # xd

    return username
