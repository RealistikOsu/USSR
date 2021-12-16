# Helps with users LOL
import time
from consts.privileges import Privileges
from helpers.discord import log_user_edit
from logger import warning, info
from typing import Optional
from globs.caches import priv, name
from globs.conn import redis, sql
from consts.modes import Mode
from consts.actions import Actions
from consts.c_modes import CustomModes
from .pep import notify_ban
from libs.time import get_timestamp

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

async def get_friends(user_id: int) -> list[int]:
    """Fetches the user IDs of users which are friends of the user"""
    friends_db = await sql.fetchall("SELECT user2 FROM users_relationships WHERE user1 = %s", (user_id,))
    return [friend[0] for friend in friends_db]

async def unlock_achievement(user_id: int, ach_id: int):
    """Adds the achievement to database."""
    await sql.execute(
        "INSERT INTO users_achievements (user_id, achievement_id, `time`) VALUES"
		"(%s, %s, %s)", (user_id, ach_id, int(time.time()))
    )

async def edit_user(action: Actions, user_id: int, reason: str = "No reason given") -> None:
    """Edits the user in the server."""

    await priv.load_singular(user_id)
    privs = await priv.get_privilege(user_id)

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
        await remove_user_from_leaderboards(user_id)
    
    username = await name.name_from_id(user_id)
    await log_user_edit(user_id, username, action, reason)
        
    # Lastly reload perms.
    await priv.load_singular(user_id)
    info(f"User ID {user_id} has been {action.log_action}!")

async def remove_user_from_leaderboards(user_id: int) -> None:
    """Removes the user from the redis leaderboards. Handles both global
    and country leaderboards."""

    country = await fetch_user_country(user_id)
    uid = str(user_id)
    for mode in ("std", "taiko", "ctb", "mania"):
        await redis.zrem(f"ripple:leaderboard:{mode}", uid)
        await redis.zrem(f"ripple:leaderboard_relax:{mode}", uid)
        await redis.zrem(f"ripple:leaderboard_ap:{mode}", uid)
        if country and (c := country.lower()) != "xx":
            await redis.zrem(f"ripple:leaderboard:{mode}:{c}", uid)
            await redis.zrem(f"ripple:leaderboard_relax:{mode}:{c}", uid)
            await redis.zrem(f"ripple:leaderboard_ap:{mode}:{c}", uid)

async def fetch_user_country(user_id: int) -> Optional[str]:
    """Fetches the user's 2 letter (uppercase) country code.
    
    Args:
        user_id (int): The database ID of the user.
    
    Returns the Alpha2 country code if found, else `None`.
    """

    return await sql.fetchcol(
        "SELECT country FROM users_stats WHERE id = %s LIMIT 1",
        (user_id,)
    )

async def log_user_error(user_id: Optional[int], traceback: str, config: str,
                         osu_ver: str, osu_hash: str) -> None:
    """Logs an error in the osu!client in the database. Uses data from the
    `/web/osu-error.php` endpoint.
    """

    ts = get_timestamp()

    await sql.execute(
        "INSERT INTO client_err_logs (user_id, timestamp, traceback, config, "
        "osu_ver, osu_hash) VALUES (%s,%s,%s,%s,%s,%s)",
        (user_id, ts, traceback, config, osu_ver, osu_hash)
    )

async def update_lb_pos(user_id: int, pp: int, mode: Mode, 
                        c_mode: CustomModes) -> None:
    """Updates the user's position on the global leaderboards.
    
    Args:
        user_id (int): The database ID for the user.
        pp (int): The user's new raw PP amount.
        mode (Mode): The mode for which the raw PP amount was provided.
        c_mode (CustomMode): The custom mode for which the raw pp amount was
            provided.
    """

    # Do not add if pp = 0
    if not pp: return
    key = f"ripple:leaderboard{c_mode.to_db_suffix()}:{mode.to_db_str()}"
    await redis.zadd(key, pp, user_id)

async def update_country_lb_pos(user_id: int, pp: int, mode: Mode, c_mode: CustomModes,
                                country: Optional[str] = None) -> None:
    """Updates the user's leaderboard position on the leaderboards for their
    country.
    
    Args:
        user_id (int): The database ID for the user.
        pp (int): The user's new raw PP amount.
        mode (Mode): The mode for which the raw PP amount was provided.
        c_mode (CustomMode): The custom mode for which the raw pp amount was
            provided.
        country (str): The Alpha2 code for the user's country. If set to None,
            it will be fetched from the database.
    """

    # Do not add if pp = 0
    if not pp: return
    if not country: country = await fetch_user_country(user_id)
    if country.lower() == "xx" or not country: return

    key = f"ripple:leaderboard{c_mode.to_db_suffix()}:{mode.to_db_str()}:{country}"
    await redis.zadd(key, pp, user_id)

async def update_last_active(user_id: int) -> None:
    """Sets the 'latest_activity' value for a user to the current timestamp."""

    ts = get_timestamp()

    await sql.execute(
        "UPDATE users SET latest_activity = %s WHERE id = %s LIMIT 1",
        (ts, user_id)
    )
