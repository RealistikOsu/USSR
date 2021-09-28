from dataclasses import dataclass
from consts.modes import Mode
from consts.c_modes import CustomModes
from typing import Optional
from globs.conn import sql
from helpers.user import get_rank_redis

@dataclass
class Stats:
    """A class representing a user's current statistics in a gamemode + c_mode
    combinations."""

    user_id: int
    mode: Mode
    c_mode: CustomModes
    ranked_score: int
    total_score: int
    pp: float
    rank: int
    accuracy: float
    playcount: int
    max_combo: int

    @classmethod
    async def from_sql(cls, user_id: int, mode: Mode, c_mode: CustomModes) -> Optional['Stats']:
        """Fetches user stats directly from the MySQL database.
        
        Args:
            user_id (int): The user ID for the user to fetch the modus operandi for.
            mode (Mode): The gamemode for which to fetch the data for.
            c_mode (CustomMode): The custom mode to fetch the data for.
        """

        stats_db = await sql.fetchone(
            ("SELECT ranked_score_{m}, total_score_{m}, pp_{m}, avg_accuracy_{m}, "
            "playcount_{m}, max_combo_{m} FROM {table} WHERE id = %s LIMIT 1")
            .format(m = mode.to_db_str(), table= c_mode.db_table),
            (user_id,)
        )
        if not stats_db: return
        rank = await get_rank_redis(user_id, mode, c_mode)

        return Stats(
            user_id,
            mode,
            c_mode,
            stats_db[0],
            stats_db[1],
            stats_db[2],
            rank,
            stats_db[3],
            stats_db[4],
            stats_db[5],
        )
