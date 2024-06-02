from __future__ import annotations

import app.state


async def get_country(user_id: int) -> str:
    country: str | None = await app.state.services.database.fetch_val(
        "SELECT country FROM users WHERE id = :id",
        {"id": user_id},
    )
    return country or "XX"
