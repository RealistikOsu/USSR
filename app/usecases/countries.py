from __future__ import annotations

import asyncio

import app.state
import logger

COUNTRIES: dict[int, str] = {}
FIVE_MINUTES = 60 * 5


async def get_country(user_id: int) -> str:
    if user_id in COUNTRIES:
        return COUNTRIES[user_id]

    country = await app.state.services.database.fetch_val(
        "SELECT country FROM users_stats WHERE id = :id",
        {"id": user_id},
    )

    if not country:
        COUNTRIES[user_id] = "XX"
        return "XX"  # xd

    COUNTRIES[user_id] = country
    return country


async def load_countries() -> None:
    db_countries = await app.state.services.database.fetch_all(
        "SELECT id, country FROM users_stats",
    )

    for db_user in db_countries:
        COUNTRIES[db_user["id"]] = db_user["country"]

    logger.info(f"Cached countries for {len(db_countries)} users!")


async def update_countries_task() -> None:
    while True:
        await load_countries()
        await asyncio.sleep(FIVE_MINUTES)
