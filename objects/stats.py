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
    
    async def recalc_pp_acc_full(self) -> tuple[float, float]:
        """Recalculates the full PP amount and average accuract for a user
        from scratch, using their top 100 scores. Sets the values in object
        and returns a tuple of pp and acc.
        
        Note:
            Performs a generally costly query due to ordering and joining
                with large tables.
            Only gets scores from ranked and approved maps.
            Doesn't set the value in the database.
        """

        scores_db = await sql.fetchall(
            ("SELECT s.accuracy, s.pp FROM {t} s RIGHT JOIN beatmaps b ON "
            "s.beatmap_md5 = b.beatmap_md5 WHERE s.completed = 3 AND "
            "s.mode = {m_val} AND b.ranked IN (3,2) ORDER BY s.pp DESC LIMIT 100")
            .format(t = self.c_mode.db_table, m_val = self.mode.value)
        )

        t_acc = 0.0
        t_pp = 0.0

        for idx, (s_acc, s_pp) in enumerate(scores_db):
            t_pp += s_pp ** idx
            t_acc += s_acc

        self.accuracy = t_acc / 100
        self.pp = t_pp

        return self.accuracy, self.pp

    async def calc_max_combo(self) -> int:
        """Calculates the maximum combo achieved and returns it, alongside
        setting the value in the object.
        
        Note:
            Involves a pretty expensive db query.
            Doesn't set the value in the database.
        """

        max_combo_db = await sql.fetchcol(
            "SELECT max_combo FROM {t} WHERE mode = {m} AND completed = 3 "
            "ORDER BY max_combo DESC LIMIT 1"
            .format(t= self.c_mode.db_table, m= self.mode.value)
        )

        if not max_combo_db: self.max_combo = 0
        else: self.max_combo = max_combo_db

        return self.max_combo
    
    async def update_rank(self) -> int:
        """Updates the user's rank using data from redis. Returns the rank
        alongside setting it for the object."""

        self.rank = await get_rank_redis(self.user_id, self.mode, self.c_mode)
        return self.rank
