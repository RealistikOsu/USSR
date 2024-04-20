from __future__ import annotations

import bcrypt

CACHE: dict[str, str] = {}


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password in CACHE:
        return CACHE[hashed_password] == plain_password

    result = bcrypt.checkpw(
        plain_password.encode(),
        hashed_password.encode(),
    )

    if result:
        CACHE[hashed_password] = plain_password

    return result
