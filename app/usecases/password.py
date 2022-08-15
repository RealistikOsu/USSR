from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Optional

import bcrypt

import app.state

# Cache management
async def cache(plain_password: str, hashed_password: str) -> None:
    await app.state.services.redis.set(
        f"ussr:passwords:{hashed_password}",
        plain_password,
        timedelta(days=1),
    )


async def get_cache(hashed_password: str) -> Optional[str]:
    return await app.state.services.redis.get(
        f"ussr:passwords:{hashed_password}",
    )


async def verify(plain_password: str, hashed_password: str) -> bool:
    cached_pw = await get_cache(hashed_password)
    if cached_pw:
        return cached_pw == plain_password

    result = await asyncio.to_thread(
        bcrypt.checkpw,
        plain_password.encode(),
        hashed_password.encode(),
    )

    if result:
        await cache(plain_password, hashed_password)

    return result
