# Helps with users LOL
from typing import Optional
from globs.conn import redis
from consts.modes import mode_to_db
from consts.c_modes import to_db_suffix

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

async def get_rank_redis(self, user_id: int, gamemode: int, c_mode: int) -> Optional[int]:
    """Fetches the rank of a user from the redis database.
    
    Args:
        user_id (int): The database ID of the user.
        gamemode (int): The gamemode enum to fetch the rank for.
        c_mode (int): The custom mode to fetch the ranks for.
    
    Returns:
        Rank as `int` if user is ranked, else `None`.
    """

    mode_str = mode_to_db(gamemode)
    suffix = to_db_suffix(c_mode)
    rank = await redis.zrevrank(
        f"ripple:leaderboard{suffix}:{mode_str}", user_id
    )
    return int(rank) + 1 if rank else None
