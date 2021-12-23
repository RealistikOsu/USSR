# The USSR Leaderboard object.
from dataclasses import dataclass

from logger import debug
from .beatmap import Beatmap
from globals.connections import sql
from globals.caches import leaderboards, add_nocheck_md5
from constants.c_modes import CustomModes
from constants.modes import Mode
from constants.statuses import FetchStatus
from constants.privileges import Privileges
from constants.complete import Completed
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from objects.score import Score

BASE_QUERY = """
SELECT
    s.id,
    s.{scoring},
    s.max_combo,
    s.50_count,
    s.100_count,
    s.300_count,
    s.misses_count,
    s.katus_count,
    s.gekis_count,
    s.full_combo,
    s.mods,
    s.time,
    a.username,
    a.id,
    s.pp
FROM
    {table} s
INNER JOIN
    users a on s.userid = a.id
    {extra_joins}
WHERE
    {where_clauses}
ORDER BY {order} DESC
"""
USER_ID_IDX = 13
USERNAME_IDX = 12
SCORING_IDX = 1

SIZE_LIMIT = 150 # Maximum score objects that can be stored

def _create_glob_lb_idx(bmap_md5: str, c_mode: CustomModes, mode: Mode) -> tuple:
    """Creates a tuple to be used as the index of the leaderboard in the cache.
    
    Args:
        bmap_md5 (str): The MD5 hash of the beatmap.
        c_mode (CustomModes): The custom mode of the leaderboard.
        mode (Mode): The mode of the leaderboard.
    
    Returns:
        tuple: The leaderboard index.
    """
    return (bmap_md5, c_mode, mode)

async def _try_bmap(md5: str) -> tuple[FetchStatus, Optional[Beatmap]]:
    """Attempts to fetch beatmap with the given md5 hash, using the lower level
    Beatmap object APIs and providing info on how the data was sourced."""

    res_bmap = None
    res_status = FetchStatus.NONE

    if res_bmap := await Beatmap.from_cache(md5):
        res_status = FetchStatus.CACHE
    elif res_bmap := await Beatmap.from_db(md5):
        res_status = FetchStatus.MYSQL
        res_bmap.cache()
    elif res_bmap := await Beatmap.from_oapi_v1(md5):
        res_status = FetchStatus.API
        res_bmap.cache()
        await res_bmap.insert_db()

    # Check if we have to try to update it.
    if res_bmap and res_bmap.deserves_update: await res_bmap.try_update()

    return res_status, res_bmap

@dataclass
class PersonalBestResult:
    """A class meant to represent a personal best score on a map."""

    score: tuple[object, ...]
    placement: int

@dataclass
class GlobalLeaderboard:
    """A class for storing beatmap leaderboards. Designed with inheritence
    in mind."""

    mode: Mode
    c_mode: CustomModes
    _scores: dict[int, tuple[object, ...]] # TODO: Maybe look into making this a score object?
    users: list[int] # ALL USERS, not just ones in `scores`
    total_scores: int
    bmap: Beatmap
    _pb_cache: dict[int, PersonalBestResult]

    # Logging info.
    bmap_fetch: FetchStatus
    lb_fetch: FetchStatus

    @property
    def has_scores(self) -> bool:
        """Property corresponding to whether """
        return not not self.users
    
    @property
    def scores(self):
        """A property returning all of the scores stored in the object."""
        return self._scores.values()

    def user_in_top(self, user_id: int) -> bool:
        """Checks if a user with the given `user_id` has their score in the top
        `SIZE_LIMIT` scores.
        
        Args:
            user_id (int): The user's ID.
        """

        return user_id in self._scores
    
    def user_has_score(self, user_id: int) -> bool:
        """Checks if the user has a best score set on the current beatmap.
        
        Args:
            user_id (int): The user's ID.
        """

        return user_id in self.users
    
    def get_user_score(self, user_id: int) -> tuple[object, ...]:
        """Fetches a user's score from the top `SIZE_LIMIT` scores.
        
        Note:
            Raises `KeyError` if score does not exist in the top x scores.
            It is recommended to use in combination with `user_in_top`.
            
        Args:
            user_id (int): The user's ID.
        
        Returns:
            tuple[object, ...]: The score object.
        """
    
        return self._scores[user_id]
    
    # Made this a function to make inheritence easier.
    def _fetch_where_conds(self) -> tuple[tuple[str], tuple[object]]:
        """Returns the where conditions to be used within MySQL queries
        related to the leaderboard, alongside args meant to be safely formatted
        into the query."""

        where_conds = (
            f"a.privileges & {Privileges.USER_PUBLIC.value}",
            f"s.beatmap_md5 = %s",
            f"s.completed = {Completed.BEST.value}",
            f"s.play_mode = {self.mode.value}"
        )
        where_args = (self.bmap.md5,)
        return where_conds, where_args
    
    def _construct_query(self, table: str, scoring: str, where_cond: str) -> str:
        """Constructs the MySQL query to execute to fetch the current leaderboard
        scores.
        
        Args:
            table (str): The MySQL database table to fetch the score from.
            scoring (str): The column that will be used for ordering and
                appear in the scoring index.
            where_cond (str): The string of the where conditions to be
                formatted in.
        """

        return BASE_QUERY.format(
            table= table,
            scoring= scoring,
            where_clauses= where_cond,
            order= scoring,
            extra_joins= "",
        )
    
    async def __fetch_scores(self) -> tuple[tuple[object, ...]]:
        """Fetches the score directly from the MySQL database based on the
        parameters of the Leaderboard object."""

        table = self.c_mode.db_table
        scoring = "pp" if self.c_mode.uses_ppboard else "score"

        where_conds, where_args = self._fetch_where_conds()
        where_cond_str = " AND ".join(where_conds)

        # No limit as we use it to fill `self.users`.
        query = self._construct_query(
            table= table,
            scoring= scoring,
            where_cond= where_cond_str,
        )

        return await sql.fetchall(query, where_args)
    
    async def __set_data_from_sql(self) -> None:
        """Causes the leaderboard scores to be fetched from the MySQL database,
        fills the `Leaderboard` object with the data from the query."""

        scores_db = await self.__fetch_scores()

        self.total_scores = len(scores_db)

        # Wipe previous data in case this is a refresh.
        self._scores.clear()
        self.users.clear()

        # Iterate over all scores and use the data.
        for idx, score in enumerate(scores_db):
            # Only store the tuples of scores in the top `SIZE_LIMIT`
            if idx + 1 < SIZE_LIMIT: self._scores[score[USER_ID_IDX]] = score
            # Store all user_ids
            self.users.append(score[USER_ID_IDX])
        
        self.lb_fetch = FetchStatus.MYSQL
    
    async def refresh(self) -> None:
        """Refreshes the leaderboard data from the database."""

        if self.bmap.has_leaderboard: await self.__set_data_from_sql()
    
    def __create_idx(self) -> tuple:
        """Creates the tuple used to index the leaderboard in the cache."""

        return _create_glob_lb_idx(self.bmap.md5, self.c_mode, self.mode)
    
    def cache(self) -> None:
        """Inserts the current leaderboard object into the global leaderboard
        cache."""

        leaderboards.cache(self.__create_idx(), self)
    
    @classmethod
    def from_cache(_, bmap_md5: str, c_mode: CustomModes, mode: Mode) -> Optional["GlobalLeaderboard"]:
        """Retrieves the leaderboard from the global leaderboard cache.
        
        Args:
            bmap_md5 (str): The MD5 hash of the beatmap.
            c_mode (CustomModes): The custom mode of the leaderboard.
            mode (Mode): The mode of the leaderboard.
        """

        res = leaderboards.get(_create_glob_lb_idx(bmap_md5, c_mode, mode))
        if res:
            # Set fetch status to cached.
            res.lb_fetch = res.bmap_fetch = FetchStatus.CACHE
            return res
        return None
    
    @classmethod
    async def from_db(cls, bmap_md5: str, c_mode: CustomModes, mode: Mode,
                      cache: bool = True, load: bool = True) -> Optional["GlobalLeaderboard"]:
        """Retrieves the leaderboard from the database.
        
        Args:
            bmap_md5 (str): The MD5 hash of the beatmap.
            c_mode (CustomModes): The custom mode of the leaderboard.
            mode (Mode): The mode of the leaderboard.
            cache (bool): Whether after fetching, the Leaderboard should be
                globally cached.
            load (bool): Whether all of the scores should be loaded.
        """

        # Fetch the beatmap.
        bmap_fetch, bmap = await _try_bmap(bmap_md5)
        if not bmap: return None

        # Create object with some empty fields.
        res = cls(
            mode= mode,
            c_mode= c_mode,
            _scores= {},
            users= [],
            total_scores= 0,
            bmap= bmap,
            bmap_fetch= bmap_fetch,
            lb_fetch= FetchStatus.NONE,
            _pb_cache= {}
        )

        if load: await res.refresh()

        if cache: res.cache()
        return res
    
    @classmethod
    async def from_md5(cls, bmap_md5: str, c_mode: CustomModes,
                       mode: Mode) -> Optional["GlobalLeaderboard"]:
        """Attempts to retrieve the leaderboard from multiple sources
        in order of performance.

        Note:
            The order of sources is:
                1. The global leaderboard cache.
                2. The database.
        
        Args:
            bmap_md5 (str): The MD5 hash of the beatmap.
            c_mode (CustomModes): The custom mode of the leaderboard.
            mode (Mode): The mode of the leaderboard.
        """

        # Try to get the leaderboard from the cache.
        res = cls.from_cache(bmap_md5, c_mode, mode)
        if res: return res

        # Try to get the leaderboard from the database.
        res = await cls.from_db(bmap_md5, c_mode, mode)
        if res: return res

        return None
    
    def get_user_placement(self, user_id: int) -> int:
        """Calculates the placement of a user's score on the leaderboard.
        
        Note:
            Raises `ValueError` if no such score exists. It is recommended
            to use `user_has_score` prior.
        """

        return self.users.index(user_id) + 1
    
    def remove_user_score(self, user_id: int) -> None:
        """Removes a user's score from the leaderboard.

        Note:
            Raises `ValueError` if no such score exists. It is recommended
            to use `user_has_score` prior.

        Args:
            user_id (int): The database ID of the user.
        """

        if user_id in self._scores:
            try: del self._scores[user_id]
            except KeyError: pass
            try: del self._pb_cache[user_id]
            except KeyError: pass
            self.users.remove(user_id)
            self.total_scores -= 1
    
    def insert_user_score(self, s: 'Score') -> None:
        """Inserts a score into the leaderboard in the appropriate order.
        
        Args:
            s (Score): The score to insert into the leaderboard.
        """

        # Check if user is in the leaderboard so we can remove his score.
        if self.user_has_score(s.user_id): self.remove_user_score(s.user_id)
        
        # Calculate positioning. TODO: Optimize this. The dict reconstruction
        # is only necessary as i don't think there is an option to insert
        # at an index to a dict.
        self.total_scores += 1
        place_idx = -1

        if self.has_scores:
            scoring = s.pp if self.c_mode.uses_ppboard else s.score
            for idx, score in enumerate(self.scores):
                if score[SCORING_IDX] < scoring:
                    place_idx = idx
                    break
        else: place_idx = 0 # They have first place

        # Last place
        if place_idx == -1 and self.total_scores < SIZE_LIMIT: place_idx = self.total_scores
        
        # Score is not in leaderboard top. Ignore.
        if place_idx == -1: return
        score_dict = {i: self._scores[i] for i in tuple(self._scores.keys())[:place_idx]}
        score_dict[s.user_id] = s.as_score_tuple(self.c_mode.uses_ppboard)
        score_dict.update({i: self._scores[i] for i in tuple(self._scores.keys())[place_idx:]})
        self._scores = score_dict

        self.users.insert(place_idx, s.user_id)

        # Trim lb in case.
        if len(self._scores) > SIZE_LIMIT: del self._scores[self.users[SIZE_LIMIT]]

        debug(f"Inserted score by {s.username} ({s.user_id}) on {s.bmap.song_name} "
               "into the cached leaderboards!")
        
    async def get_user_pb(self, user_id: int, cache: bool = True) -> tuple[FetchStatus, Optional[PersonalBestResult]]:
        """Attempts to fetch a user's personal best for this leaderboard
        using data provided by the object and MySQL.
        
        Args:
            user_id (int): The database ID of the user.
            cache (bool): Whether to cache the result for use later.
        """
        
        # Check if they are in the lb as a quick way to avoid querying.
        if not self.user_has_score(user_id): return FetchStatus.NONE, None
        if pb := self._pb_cache.get(user_id): return FetchStatus.CACHE, pb

        st = FetchStatus.LOCAL

        # Check if we can construct a score from data in the object.
        if self.user_in_top(user_id):
            score = self.get_user_score(user_id)
        else:
            st = FetchStatus.MYSQL
            # MySQL time!
            where_conds, where_args = self.__fetch_where_conds()

            # Extend them to limit them to the user.
            where_conds = (*where_conds, f"s.userid = %s")
            where_args = (*where_args, user_id)
            where_cond_str = " AND ".join(where_conds)
            scoring = "pp" if self.c_mode.uses_ppboard else "score"
            table = self.c_mode.db_table

            query = BASE_QUERY.format(
                scoring= scoring,
                table= table,
                where_clauses= where_cond_str,
                order= "s.id",
                extra_joins= "",
            ) + "LIMIT 1"

            score = await sql.fetchone(query, where_args)
        
        pb = PersonalBestResult(score, self.get_user_placement(user_id))
        if cache: self._pb_cache[user_id] = pb

        return st, pb
    
    async def refresh_beatmap(self, md5: Optional[str] = None) -> None:
        """Refreshes the beatmap object for the leaderboard, fetching it
        again using `_try_bmap`
        
        Args:
            md5 (str): The MD5 of the new beatmap. If not provided, the MD5
                of the previous `Beatmap` object will be utilised.
        """

        self.bmap_fetch, self.bmap = await _try_bmap(md5 or self.bmap.md5)

@dataclass
class CountryLeaderboard(GlobalLeaderboard):
    """An object representing a country leaderboard."""

    user_id: int = 0
    
    # Remove caching rn, although this would probably be the best candidate for
    # non global lb caching.
    @classmethod
    def from_cache(_, _1, _2, _3) -> None: return
    def cache(_) -> None: return

    @classmethod
    async def from_db(cls, bmap_md5: str, c_mode: CustomModes, mode: Mode,
                      user_id: int, load: bool = True) -> Optional["GlobalLeaderboard"]:
        """Creates an instance of `GlobalLeaderboard` using data from MySQL.
        
        Args:
            bmap_md5 (str): The MD5 hash of the beatmap.
            c_mode (CustomModes): The custom mode of the leaderboard.
            mode (Mode): The mode of the leaderboard.
            user_id (int): The database ID of the user who's country should be
                used in the leaderboards.
            load (bool): Whether the leaderboard scores should be fetched from the
                MySQL database.
        """

        # Fetch the beatmap.
        bmap_fetch, bmap = await _try_bmap(bmap_md5)
        if not bmap: return None

        # Create object with some empty fields.
        res = cls(
            mode= mode,
            c_mode= c_mode,
            _scores= {},
            users= [],
            total_scores= 0,
            bmap= bmap,
            bmap_fetch= bmap_fetch,
            lb_fetch= FetchStatus.NONE,
            _pb_cache= {},
            user_id= user_id,
        )

        if load: await res.refresh()
        return res
    
    def _construct_query(self, table: str, scoring: str, where_cond: str) -> str:
        """Constructs the MySQL query to execute to fetch the current leaderboard
        scores.
        
        Args:
            table (str): The MySQL database table to fetch the score from.
            scoring (str): The column that will be used for ordering and
                appear in the scoring index.
            where_cond (str): The string of the where conditions to be
                formatted in.
        """
        return BASE_QUERY.format(
            table= table,
            scoring= scoring,
            where_clauses= where_cond,
            order= scoring,
            extra_joins= "INNER JOIN users_stats st ON st.id = a.id",
        )
    
    def _fetch_where_conds(self) -> tuple[tuple[str], tuple[object]]:
        """Returns the where conditions to be used within MySQL queries
        related to the leaderboard, alongside args meant to be safely formatted
        into the query."""

        where_conds = (
            f"a.privileges & {Privileges.USER_PUBLIC.value}",
            "s.beatmap_md5 = %s",
            f"s.completed = {Completed.BEST.value}",
            f"s.play_mode = {self.mode.value}",
            "st.country = (SELECT country FROM users_stats WHERE id = %s)"
        )
        where_args = (self.bmap.md5, self.user_id,)
        return where_conds, where_args

class FriendLeaderboard(CountryLeaderboard):
    """Leaderboard handling the leaderboard for user's friends. Inherits from
    `CountryLeaderboard` due to it handling the userid and caching logic."""

    def _construct_query(self, table: str, scoring: str, where_cond: str) -> str:
        """Constructs the MySQL query to execute to fetch the current leaderboard
        scores.
        
        Args:
            table (str): The MySQL database table to fetch the score from.
            scoring (str): The column that will be used for ordering and
                appear in the scoring index.
            where_cond (str): The string of the where conditions to be
                formatted in.
        """
        return BASE_QUERY.format(
            table= table,
            scoring= scoring,
            where_clauses= where_cond,
            order= scoring,
            extra_joins= "",
        )
    
    def _fetch_where_conds(self) -> tuple[tuple[str], tuple[object]]:
        """Returns the where conditions to be used within MySQL queries
        related to the leaderboard, alongside args meant to be safely formatted
        into the query."""

        where_conds = (
            f"a.privileges & {Privileges.USER_PUBLIC.value}",
            "s.beatmap_md5 = %s",
            f"s.completed = {Completed.BEST.value}",
            f"s.play_mode = {self.mode.value}",
            ("(a.id IN (SELECT user2 FROM users_relationships WHERE user1 = %s)"
             "OR a.id = %s)")
        )
        where_args = (self.bmap.md5, self.user_id, self.user_id,)
        return where_conds, where_args

@dataclass
class ModLeaderboard(GlobalLeaderboard):
    """Leaderboard handling the leaderboard for current selected mods."""

    mods: int = 0

    @classmethod
    async def from_db(cls, bmap_md5: str, c_mode: CustomModes, mode: Mode,
                      mods: int, load: bool = True) -> Optional["GlobalLeaderboard"]:
        """Creates an instance of `GlobalLeaderboard` using data from MySQL.
        
        Args:
            bmap_md5 (str): The MD5 hash of the beatmap.
            c_mode (CustomModes): The custom mode of the leaderboard.
            mode (Mode): The mode of the leaderboard.
            mods (int): The score mods which should be used in the leaderboards.
            load (bool): Whether the leaderboard scores should be fetched from the
                MySQL database.
        """

        # Fetch the beatmap.
        bmap_fetch, bmap = await _try_bmap(bmap_md5)
        if not bmap: return None

        # Create object with some empty fields.
        res = cls(
            mode= mode,
            c_mode= c_mode,
            _scores= {},
            users= [],
            total_scores= 0,
            bmap= bmap,
            bmap_fetch= bmap_fetch,
            lb_fetch= FetchStatus.NONE,
            _pb_cache= {},
            mods= mods
        )

        if load: await res.refresh() 
        return res

    def _fetch_where_conds(self) -> tuple[tuple[str], tuple[object]]:
        """Returns the where conditions to be used within MySQL queries
        related to the leaderboard, alongside args meant to be safely formatted
        into the query."""

        where_conds = (
            f"a.privileges & {Privileges.USER_PUBLIC.value}",
            "s.beatmap_md5 = %s",
            f"s.completed = {Completed.BEST.value}",
            f"s.play_mode = {self.mode.value}",
            "s.mods = %s"
        )
        where_args = (self.bmap.md5, self.mods)
        return where_conds, where_args
