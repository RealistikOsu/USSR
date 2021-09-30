from dataclasses import dataclass
from logger import warning
from consts.modes import Mode
from consts.mods import Mods
from consts.c_modes import CustomModes
from consts.complete import Completed
from consts.privileges import Privileges
from objects.beatmap import Beatmap
from globs.conn import sql
from globs import caches
from libs.crypt import validate_md5
from lenhttp import Request

@dataclass
class Score:
    """A class representing a singular score set on a beatmap."""

    id: int
    bmap: Beatmap
    user_id: int
    score: int
    max_combo: int
    full_combo: bool
    passed: bool
    quit: bool
    mods: Mods
    c_mode: CustomModes
    count_300: int
    count_100: int
    count_50: int
    count_katu: int
    count_geki: int
    count_miss: int
    timestamp: int
    mode: Mode
    completed: Completed
    accuracy: float
    pp: float
    play_time: int
    placement: int
    grade: str

    @property
    def is_submitted(self) -> bool:
        """Bool corresponding to whether the score has been submitted."""

        return self.id != 0
    
    async def calc_completed(self) -> Completed:
        """Calculated the `complete` attribute for scores.
        
        Note:
            This DOES update the data for other scores. Only perform this
                function IF you are absolutely certain that this score is
                going to be added to the database.
            Running first place first is recommended for a potential perf
                save.
        """

        # Get the simple ones out the way.
        if self.placement == 0:
            self.completed = Completed.BEST
            return self.completed
        elif self.quit:
            self.completed = Completed.FAILED
            return self.completed
        elif not self.passed:
            self.completed = Completed.FAILED
            return self.completed
        
        # Don't bother for non-lb things.
        if not self.bmap.has_leaderboard:
            self.completed = Completed.COMPLETE
            return self.completed
        
        table = self.c_mode.db_table
        scoring = "pp" if self.c_mode.uses_ppboard else "score"
        val = self.pp if self.c_mode.uses_ppboard else self.score
        
        # Welp. Gotta do sql.
        await sql.execute(
            f"UPDATE {table} SET completed = {Completed.COMPLETE.value} WHERE "
            f"userid = %s AND completed = {Completed.BEST.value} AND beatmap_md5 = %s "
            f"AND playmode = {self.mode.value}"
        )
    
    async def calc_placement(self, handle_first_place: bool = True) -> int:
        """Calculates the placement of the score on the leaderboards.
        
        Note:
            Performs a generally costly query.
            Returns 0 if bmap ranked status doesnt have lbs.
            Returns 0 if completed doesnt allow.
        
        Args:
            handle_first_place (bool): If `True`, the `on_first_place` function
                will be automatically performed if placement == 1.
        """

        if (not self.completed.completed) and (not self.bmap.has_leaderboard):
            self.placement = 0
            return 0

        table = self.c_mode.db_table
        scoring = "pp" if self.c_mode.uses_ppboard else "score"
        val = self.pp if self.c_mode.uses_ppboard else self.score

        self.placement = await sql.fetchcol(
            f"SELECT COUNT(*) FROM {table} s INNER JOIN users u ON s.userid = "
            f"u.id WHERE u.privileges & {Privileges.USER_PUBLIC.value} AND "
            f"s.playmode = {self.mode.value} AND s.completed = {Completed.BEST.value} "
            f"AND {scoring} > %s AND s.beatmap_md5 = %s",
            (val, self.bmap.md5)
        )

        if self.placement == 1 and handle_first_place:
            await self.on_first_place()

        return self.placement
    
    async def calc_pp(self) -> float:
        """Calculates the PP given for the score."""

        if (not self.bmap.has_leaderboard) or (not self.completed.completed):
            self.pp = .0
            return self.pp
        
        warning("Attempted PP calculation for score while PP calc is not implemented."
                " Score will not have a PP value.")
        
        # TODO
        self.pp = .0
        return self.pp
    
    async def on_first_place(self) -> None:
        """Adds the score to the first_places table."""

        # Why did I design this system when i was stupid...
        ...

        warning("Attempted to perform first place handling while first places "
                "have not yet been implemented!")

    async def submit(self, clear_lbs: bool = True, calc_completed: bool = True,
                     calc_place: bool = True) -> None:
        """Inserts the score into the database, performing other necessary
        calculations.
        
        Args:
            clear_lbs (bool): If true, the leaderboard and personal best
                cache for this beatmap + c_mode + mode combo.
            calc_completed (bool): Whether the `completed` attribute should
                be calculated (MUST NOT BE RAN BEFORE, ELSE SCORES WILL BE
                WEIRD IN THE DB)
            calc_place (bool): Whether the placement of the score should be
                calculated (may not be calculated if `completed` does not
                allow so).
        """

        if calc_completed: await self.calc_completed()
        if clear_lbs and self.completed == Completed.BEST:
            caches.clear_lbs(self.bmap.md5, self.mode, self.c_mode)
            caches.clear_pbs(self.bmap.md5, self.mode, self.c_mode)
        if calc_place: await self.calc_placement(True)

        await self.__insert()

    async def __insert(self) -> None:
        """Inserts the score directly into the database."""

        table = self.c_mode.db_table
