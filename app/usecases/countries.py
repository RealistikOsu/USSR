from __future__ import annotations

import app.state


async def get_country(user_id: int) -> str:
    country = await app.state.services.database.fetch_val(
        "SELECT country FROM users_stats WHERE id = :id",
        {"id": user_id},
    )

    if not country:
        return "XX"  # xd

    return country
