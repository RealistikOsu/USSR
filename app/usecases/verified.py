from __future__ import annotations

import app.state
import logger
from config import config


async def get_verified(user_id: int) -> bool:
    return await app.state.services.database.fetch_val(
        "SELECT 1 FROM user_badges WHERE user = :uid AND badge = :bid",
        {"uid": user_id, "bid": config.srv_verified_badge},
    )

