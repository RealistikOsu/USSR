from __future__ import annotations

import app.state


async def get_whitelisted_users() -> list[int]:
    results_db = app.state.services.database.iterate(
        "SELECT user_id FROM whitelist",
    )

    return [result["user_id"] async for result in results_db]


async def is_whitelisted(user_id: int) -> bool:
    return await app.state.services.database.fetch_val(
        "SELECT 1 FROM whitelist WHERE user_id = :uid",
        {"uid": user_id},
    )
