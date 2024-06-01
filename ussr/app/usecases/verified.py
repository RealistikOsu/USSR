from __future__ import annotations

import settings
import app.state


async def get_verified(user_id: int) -> bool:
    return await app.state.services.database.fetch_val(
        "SELECT 1 FROM user_badges WHERE user = :uid AND badge = :bid",
        {"uid": user_id, "bid": settings.PS_VERIFIED_BADGE},
    )
