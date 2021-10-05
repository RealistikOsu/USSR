# Helps with users LOL
from logger import warning
from typing import Optional
from globs.conn import redis, sql
from consts.modes import Mode
from consts.c_modes import CustomModes

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

    return s.lower().replace(" ", "_").rstrip()

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

async def update_rank(user_id: int, new_score: int, mode: Mode, c_mode: CustomModes):
    """Updates redis leaderboard list by pushing new score into."""

    suffix = c_mode.to_db_suffix()
    mode_str = mode.to_db_str()
    country = await sql.fetchcol("SELECT country FROM users_stats WHERE id = %s", (user_id,))
    await redis.zadd(f"ripple:leaderboard{suffix}:{mode_str}", new_score, user_id)
    await redis.zadd(f"ripple:leaderboard{suffix}:{mode_str}:{country.lower()}", new_score, user_id)

async def restrict_user(user_id: int, reason: str = None) -> None:
    """Restricts the user from the server."""

    warning(f"Attempted to restrict user {user_id} for {reason} when "
            "restrictions are not yet implemented.")
    
    ...

    # Do priv update.
    #await priv.load_singular(user_id)

    # TODO: call redis, might make the call above redundant
