from __future__ import annotations

import time
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Optional

from fastapi import HTTPException

import app.state.services
import app.usecases.discord
import app.usecases.password
import app.usecases.privileges
import app.usecases.score
import app.utils
import logger
from app.constants.mode import Mode
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


async def fetch_db_id(user_id: int) -> Optional[User]:
    db_user = await app.state.services.database.fetch_one(
        "SELECT * FROM users WHERE id = :id",
        {"id": user_id},
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
) -> Callable[[str, str], Awaitable[User]]:
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
        await app.state.services.redis.zrem(f"ripple:relaxboard:{mode}", uid)
        await app.state.services.redis.zrem(f"ripple:autoboard:{mode}", uid)

        if user.country and (c := user.country.lower()) != "xx":
            await app.state.services.redis.zrem(f"ripple:leaderboard:{mode}:{c}", uid)

            await app.state.services.redis.zrem(
                f"ripple:relaxboard:{mode}:{c}",
                uid,
            )

            await app.state.services.redis.zrem(
                f"ripple:autoboard:{mode}:{c}",
                uid,
            )


async def notify_ban(user: User) -> None:
    await app.state.services.redis.publish("peppy:ban", user.id)


async def insert_ban_log(user: User, detail: str) -> None:
    """Inserts a ban log into the database.

    Note:
        This function prefixes the detail with `"LESS Autoban: "` before
        inserting it into the database.
    """

    # Prefix the detail with a less autoban.
    detail = "LESS Autoban: " + detail

    await app.state.services.database.execute(
        "INSERT INTO rap_logs (userid, text, datetime, through) VALUES (:uid, :text, :time, :thru)",
        {
            "uid": user.id,
            "text": detail,
            "time": int(time.time()),
            "thru": "LESS",
        },
    )


DEFAULT_SUMMARY = "No summary available."


async def restrict_user(
    user: User,
    summary: str = DEFAULT_SUMMARY,
) -> None:
    if user.privileges.is_restricted:
        return

    user.privileges = user.privileges & ~Privileges.USER_PUBLIC
    await app.state.services.database.execute(
        "UPDATE users SET privileges = :new_priv, ban_datetime = :ban_time, ban_reason = :ban_reason WHERE id = :id",
        {
            "new_priv": user.privileges,
            "ban_time": int(time.time()),
            "ban_reason": summary,
            "id": user.id,
        },
    )

    await insert_ban_log(user, summary)
    await notify_ban(user)
    await remove_from_leaderboard(user)

    app.usecases.privileges.set_privilege(user.id, user.privileges)

    await app.usecases.discord.log_user_edit(user, "restricted", summary)
    logger.info(f"{user} has been restricted for {summary}!")


async def fetch_achievements(user_id: int, mode: Mode) -> list[int]:
    db_achievements = await app.state.services.database.fetch_all(
        "SELECT achievement_id FROM users_achievements WHERE user_id = :id AND mode = :mode",
        {"id": user_id, "mode": mode.value},
    )

    return [ach["achievement_id"] for ach in db_achievements]


async def unlock_achievement(achievement_id: int, user_id: int, mode: Mode) -> None:
    await app.state.services.database.execute(
        "INSERT INTO users_achievements (achievement_id, user_id, mode, created_at) "
        "VALUES (:achievement_id, :user_id, :mode, :timestamp)",
        {
            "achievement_id": achievement_id,
            "user_id": user_id,
            "mode": mode.value,
            "timestamp": int(time.time()),
        },
    )


async def increment_replays_watched(user_id: int, mode: Mode) -> None:
    await app.state.services.database.execute(
        (
            """
            UPDATE users_stats
            SET replays_watched_{0} = replays_watched_{0} + 1
            WHERE id = :id
            """
        ).format(mode.stats_prefix),
        {"id": user_id},
    )
