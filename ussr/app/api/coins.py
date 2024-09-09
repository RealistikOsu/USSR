from __future__ import annotations

import logger
import app.state.services
from app.models.user import User
from app.usecases.user import authenticate_user
from fastapi import Depends
from fastapi import Query


async def coins(
    user: User = Depends(authenticate_user(Query, "u", "h")),
    action: str = Query(...),
    count: int = Query(..., alias="c"),
    checksum: str = Query(..., alias="cs"),
):
    if action not in ("earn", "use", "recharge"):
        return str(user.coins)

    if action == "earn":
        logger.info(f"{user} has earned a coin.")
        user.coins += 1
    elif action == "use":
        logger.info(f"{user} has used a coin.")
        user.coins -= 1
    else:  # recharge
        if user.coins <= 0:
            logger.info(f"{user} has recharged their coins.")
            user.coins = 1

    await app.state.services.database.execute(
        "UPDATE users SET coins = :coins WHERE id = :id",
        {"coins": user.coins, "id": user.id},
    )

    return str(user.coins)
