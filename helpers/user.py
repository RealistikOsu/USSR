# Helps with users LOL
import time
from consts.privileges import Privileges
from helpers.discord import log_user_edit
from logger import warning, info
from typing import Optional
from globs.caches import priv
from globs.conn import redis, sql
from consts.modes import Mode
from consts.actions import Actions
from consts.c_modes import CustomModes
from .pep import notify_ban

def safe_name(s: str) -> str:
    """Generates a 'safe' variant of the name for usage in rapid lookups
    and usage in Ripple database.

    Note:
        A safe name is a name that is:
            - Lowercase
            - Has spaces replaced with underscores
            - Is rstripped.
    
    Args:
        s (str): The username to create a safe variant of.
    """

    return s.rstrip().lower().replace(" ", "_")

async def get_rank_redis(user_id: int, gamemode: Mode, 
                         c_mode: CustomModes) -> Optional[int]:
    """Fetches the rank of a user from the redis database.
    
    Args:
        user_id (int): The database ID of the user.
        gamemode (Mode): The gamemode enum to fetch the rank for.
        c_mode (CustomModes): The custom mode to fetch the ranks for.
    
    Returns:
        Rank as `int` if user is ranked, else `None`.
    """

    mode_str = gamemode.to_db_str()
    suffix = c_mode.to_db_suffix()
    rank = await redis.zrevrank(
        f"ripple:leaderboard{suffix}:{mode_str}", user_id
    )
    return int(rank) + 1 if rank else None

async def incr_replays_watched(user_id: int, mode: Mode) -> None:
    """Increments the replays watched statistic for the user on a given mode."""

    suffix = mode.to_db_str()
    await sql.execute(
        ("UPDATE users_stats SET replays_watched_{0} = replays_watched_{0} + 1 "
        "WHERE id = %s LIMIT 1").format(suffix), (user_id,)
    )

async def get_achievements(user_id: int):
    """Gets all user unlocked achievements from sql."""
    return [ach[0] for ach in await sql.fetchall("SELECT achievement_id FROM users_achievements WHERE user_id = %s", (user_id,))]

async def unlock_achievement(user_id: int, ach_id: int):
    """Adds the achievement to database."""
    await sql.execute(
        "INSERT INTO users_achievements (user_id, achievement_id, `time`) VALUES"
		"(%s, %s, %s)", (user_id, ach_id, int(time.time()))
    )

async def update_rank(user_id: int, new_score: int, mode: Mode, c_mode: CustomModes):
    """Updates redis leaderboard list by pushing new score into."""

    suffix = c_mode.to_db_suffix()
    mode_str = mode.to_db_str()
    country = await sql.fetchcol("SELECT country FROM users_stats WHERE id = %s", (user_id,))
    await redis.zadd(f"ripple:leaderboard{suffix}:{mode_str}", new_score, user_id)
    if country and country.lower() != "xx":
        await redis.zadd(f"ripple:leaderboard{suffix}:{mode_str}:{country.lower()}", new_score, user_id)

async def edit_user(action: Actions, user_id: int, reason: str = "No reason given") -> None:
    """Edits the user in the server."""

    await priv.load_singular(user_id)
    privs = priv.privileges.get(user_id)

    if action in (Actions.UNRESTRICT, Actions.UNBAN) and (privs.is_banned or privs.is_restricted):
        # Unrestrict procedure.
        await sql.execute(
            "UPDATE users SET privileges = privileges | %s, "
            "ban_datetime = 0, ban_reason = '' WHERE id = %s LIMIT 1",
            (int(Privileges.USER_NORMAL | Privileges.USER_PUBLIC), user_id)
        )
        await notify_ban(user_id)

    elif action in (Actions.RESTRICT, Actions.BAN) and not (privs.is_banned or privs.is_restricted):
        # Now its just ban/restrict stuff..
        perms = int(~Privileges.USER_PUBLIC) if action == Actions.RESTRICT \
                        else int(~(Privileges.USER_NORMAL | Privileges.USER_PUBLIC))
        await sql.execute(
            "UPDATE users SET privileges = privileges & %s, "
            "ban_datetime = %s, ban_reason = %s WHERE id = %s LIMIT 1",
            (perms, int(time.time()), reason, user_id)
        )

        # Notify pep.py about that.
        await notify_ban(user_id)

        # Do lbs cleanups in redis.
        country = await sql.fetchcol("SELECT country FROM users_stats WHERE id = %s", (user_id,))
        uid = str(user_id)
        for mode in ("std", "taiko", "ctb", "mania"):
            await redis.zrem(f"ripple:leaderboard:{mode}", uid)
            await redis.zrem(f"ripple:leaderboard_relax:{mode}", uid)
            await redis.zrem(f"ripple:leaderboard_ap:{mode}", uid)
            if country and (c := country.lower()) != "xx":
                await redis.zrem(f"ripple:leaderboard:{mode}:{c}", uid)
                await redis.zrem(f"ripple:leaderboard_relax:{mode}:{c}", uid)
                await redis.zrem(f"ripple:leaderboard_ap:{mode}:{c}", uid)
    
    await log_user_edit(user_id, "<username>", action, reason)
        
    # Lastly reload perms.
    await priv.load_singular(user_id)
    info(f"User ID {user_id} has been {action.log_action}!")

async def fetch_user_country(user_id: int) -> Optional[str]:
    """Fetches the user's 2 letter (uppercase) country code.
    
    Args:
        user_id (int): The database ID of the user.
    
    Returns the Alpha2 country code if found, else `None`.
    """

    return await sql.fetchcol(
        "SELECT country FROM users WHERE id = %s LIMIT 1",
        (user_id,)
    )
