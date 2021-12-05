from dataclasses import dataclass
from consts.modes import Mode
from consts.c_modes import CustomModes
from typing import Optional
from globs.conn import sql
from helpers.user import get_rank_redis
from helpers.pep import stats_refresh
from logger import debug
from globs.caches import stats_cache

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
    total_hits: int

    # Optimisation data.
    _required_recalc_pp: int = 0
    _cur_bonus_pp: float = 0.0

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
            "playcount_{m}, max_combo_{m}, total_hits_{m} FROM {p}_stats WHERE id = %s LIMIT 1")
            .format(m = mode.to_db_str(), p= c_mode.db_prefix),
            (user_id,)
        )
        if not stats_db: return
        rank = await get_rank_redis(user_id, mode, c_mode)

        debug(f"Retrieved stats for {user_id} from the MySQL database.")

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
            stats_db[6]
        )
    
    @classmethod
    async def from_cache(self, user_id: int, mode: Mode, c_mode: CustomModes) -> Optional['Stats']:
        """Attempts to fetch an existing stats object from the global stats cache.
        
        Args:
            user_id (int): The user ID for the user to fetch the modus operandi for.
            mode (Mode): The gamemode for which to fetch the data for.
            c_mode (CustomMode): The custom mode to fetch the data for.
        """

        s = stats_cache.get((c_mode, mode, user_id))

        if s: debug(f"Fetched stats for {user_id} from cache!")
        return s
    
    @classmethod
    async def from_id(self, user_id: int, mode: Mode, c_mode: CustomModes) -> Optional['Stats']:
        """High level classmethod that attempts to fetch the stats from all
        possible sources, ordered from fastest to slowest.
        
        Args:
            user_id (int): The user ID for the user to fetch the modus operandi for.
            mode (Mode): The gamemode for which to fetch the data for.
            c_mode (CustomMode): The custom mode to fetch the data for.
        """

        for m in _fetch_ord:
            r = await m(user_id, mode, c_mode)
            if r:
                if m in _fetch_cache: r.cache()
                return r
    
    def cache(self) -> None:
        """Caches the current stats object to the global stats cache."""

        stats_cache.cache(
            (self.c_mode, self.mode, self.user_id), self
        )
    
    async def recalc_pp_acc_full(self, _run_pp: int = None) -> tuple[float, float]:
        """Recalculates the full PP amount and average accuract for a user
        from scratch, using their top 100 scores. Sets the values in object
        and returns a tuple of pp and acc.
        
        Note:
            Performs a generally costly query due to ordering and joining
                with large tables.
            Only gets scores from ranked and a approved maps.
            Doesn't set the value in the database.
        
        Args:
            _run_pp (int): The amount of PP for the score prompting this recalc.
                This is an optimisation that means that if this score is not
                enough to reach the top 100 (min for this to be considered),
                this will not run.
        """

        if self._required_recalc_pp and _run_pp is not None \
           and _run_pp < self._required_recalc_pp:
            self.pp -= self._cur_bonus_pp
            self.pp += await self.__calc_bonus_pp() # Calculate the bonus.
            debug("Bypassed full PP and acc recalc for user: score didnt meet top 100.")
            return

        scores_db = await sql.fetchall(
            ("SELECT s.accuracy, s.pp FROM {t} s RIGHT JOIN beatmaps b ON "
            "s.beatmap_md5 = b.beatmap_md5 WHERE s.completed = 3 AND "
            "s.play_mode = {m_val} AND b.ranked IN (3,2) AND s.userid = %s "
            "ORDER BY s.pp DESC LIMIT 100")
            .format(t = self.c_mode.db_table, m_val = self.mode.value),
            (self.user_id,)
        )

        t_acc = 0.0
        t_pp = 0.0

        for idx, (s_acc, s_pp) in enumerate(scores_db):
            t_pp += s_pp * (0.95 ** idx)
            t_acc += s_acc * (0.95 ** idx) # TLDR: accuracy is scaled too!

        # Big brain optimisation to stop this being uselessly ran.
        if idx == 99: self._required_recalc_pp = s_pp
  
        self.accuracy = (t_acc * (100.0 / (20 * (1 - 0.95 ** (idx + 1))))) / 100
        self.pp = t_pp + await self.__calc_bonus_pp()

        return self.accuracy, self.pp

    async def calc_max_combo(self) -> int:
        """Calculates the maximum combo achieved and returns it, alongside
        setting the value in the object.
        
        Note:
            Involves a pretty expensive db query.
            Doesn't set the value in the database.
        """

        max_combo_db = await sql.fetchcol(
            "SELECT max_combo FROM {t} WHERE play_mode = {m} AND completed = 3 "
            "AND userid = %s ORDER BY max_combo DESC LIMIT 1"
            .format(t= self.c_mode.db_table, m= self.mode.value),
            (self.user_id,)
        )

        self.max_combo = max_combo_db or 0

        return self.max_combo
    
    async def update_rank(self) -> int:
        """Updates the user's rank using data from redis. Returns the rank
        alongside setting it for the object."""

        self.rank = await get_rank_redis(self.user_id, self.mode, self.c_mode)
        return self.rank

    async def __calc_bonus_pp(self) -> float:
        """Calculates the playcount based PP for the user.
        https://osu.ppy.sh/wiki/en/Performance_points#how-much-bonus-pp-is-awarded-for-having-lots-of-scores-on-ranked-maps

        Note:
            Performs a generally expensive join.
        """

        count = await sql.fetchcol(
            "SELECT COUNT(*) FROM {t} s RIGHT JOIN beatmaps b ON s.beatmap_md5 = "
            "b.beatmap_md5 WHERE b.ranked IN (2, 3) AND " # Max limit is 25397 to get max bonus pp.
            "s.completed = 3 AND s.userid = %s LIMIT 25397".format(t= self.c_mode.db_table),
            (self.user_id,)
        )

        self._cur_bonus_pp = 416.6667 * (1 - (0.9994 ** count))
        return self._cur_bonus_pp
    
    async def save(self, refresh_cache: bool = True) -> None:
        """Saves the current stats to the MySQL database.
        
        Args:
            refresh_cache (bool): Whether the stats cached by pep.py
                should be refreshed.
        """

        await sql.execute(
            ("UPDATE {table}_stats SET ranked_score_{m} = %s, total_score_{m} = %s,"
            "pp_{m} = %s, avg_accuracy_{m} = %s, playcount_{m} = %s,"
            "max_combo_{m} = %s, total_hits_{m} = %s WHERE id = %s LIMIT 1")
            .format(m = self.mode.to_db_str(), table= self.c_mode.db_prefix),
            (self.ranked_score, self.total_score, self.pp, self.accuracy,
            self.playcount, self.max_combo, self.total_hits, self.user_id)
        )

        if refresh_cache: await stats_refresh(self.user_id)

_fetch_ord = (
    Stats.from_cache,
    Stats.from_sql,
)
_fetch_cache = (Stats.from_sql,)
