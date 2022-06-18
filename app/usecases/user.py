from __future__ import annotations

import time
from typing import Any
from typing import Callable
from typing import Optional

from fastapi import HTTPException

import app.state.services
import app.usecases.discord
import app.usecases.password
import app.utils
import logger
from app.constants.privileges import Privileges
from app.models.user import User


async def fetch_db(username: str) -> Optional[User]:
    safe_name = app.utils.make_safe(username)

    db_user = await app.state.services.database.fetch_one(
        "SELECT * FROM users WHERE username_safe = :safe_name",
        {"safe_name": safe_name},
    )

    if not db_user:
        return None

    country = await app.state.services.database.fetch_val(
        "SELECT country FROM users_stats WHERE id = :id",
        {"id": db_user["id"]},
    )

    db_friends = await app.state.services.database.fetch_all(
        "SELECT user2 FROM users_relationships WHERE user1 = :id",
        {"id": db_user["id"]},
    )

    friends = [relationship["user2"] for relationship in db_friends]

    return User(
        id=db_user["id"],
        name=db_user["username"],
        privileges=Privileges(db_user["privileges"]),
        friends=friends,
        password_bcrypt=db_user["password_md5"],
        country=country,
    )


# common call ver
async def auth_user(username: str, password: str) -> Optional[User]:
    user = await fetch_db(username)
    if not user:
        return None

    correct_password = await app.usecases.password.verify_password(
        password,
        user.password_bcrypt,
    )
    if not correct_password:
        return None

    return user


# depends ver
def authenticate_user(
    param_function: Callable[..., Any],
    name_arg: str = "u",
    password_arg: str = "p",
    error_text: Optional[Any] = None,
) -> Optional[User]:
    async def wrapper(
        username: str = param_function(..., alias=name_arg),
        password: str = param_function(..., alias=password_arg),
    ):
        user = await fetch_db(username)
        if not user:
            raise HTTPException(
                status_code=401,
                detail=error_text,
            )

        correct_password = await app.usecases.password.verify_password(
            password,
            user.password_bcrypt,
        )
        if not correct_password:
            raise HTTPException(
                status_code=401,
                detail=error_text,
            )

        return user

    return wrapper


async def remove_from_leaderboard(user: User) -> None:
    uid = str(user.id)

    for mode in ("std", "taiko", "ctb", "mania"):
        await app.state.services.redis.zrem(f"ripple:leaderboard:{mode}", uid)
        await app.state.services.redis.zrem(f"ripple:leaderboard_relax:{mode}", uid)
        await app.state.services.redis.zrem(f"ripple:leaderboard_ap:{mode}", uid)

        if user.country and (c := user.country.lower()) != "xx":
            await app.state.services.redis.zrem(f"ripple:leaderboard:{mode}:{c}", uid)

            await app.state.services.redis.zrem(
                f"ripple:leaderboard_relax:{mode}:{c}",
                uid,
            )

            await app.state.services.redis.zrem(
                f"ripple:leaderboard_ap:{mode}:{c}",
                uid,
            )


async def notify_ban(user: User) -> None:
    await app.state.services.redis.publish("peppy:ban", user.id)


async def restrict_user(user: User, reason: str = "No reason given") -> None:
    if user.privileges.is_restricted:
        return

    user.privileges = user.privileges & ~Privileges.USER_PUBLIC
    await app.state.services.database.execute(
        "UPDATE users SET privileges = :new_priv, ban_datetime = :ban_time, ban_reason = :ban_reason WHERE id = :id",
        {
            "new_priv": user.privileges,
            "ban_time": int(time.time()),
            "ban_reason": reason,
            "id": user.id,
        },
    )

    await notify_ban(user)
    await remove_from_leaderboard(user)

    await app.usecases.discord.log_user_edit(user, "restricted", reason)
    logger.info(f"{user} has been restricted for {reason}!")
