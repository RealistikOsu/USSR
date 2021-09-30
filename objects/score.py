from dataclasses import dataclass
from consts.modes import Mode
from consts.mods import Mods
from consts.c_modes import CustomModes
from consts.complete import Completed
from objects.beatmap import Beatmap
from globs import caches

@dataclass
class Score:
    """A class representing a singular score set on a beatmap."""

    id: int
    bmap: Beatmap
    user_id: int
    score: int
    max_combo: int
    full_combo: bool
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

    @property
    def is_submitted(self) -> bool:
        """Bool corresponding to whether the score has been submitted."""

        return self.id != 0
    
    async def calc_completed(self) -> None:
        """Calculated the `complete` attribute for scores.
        
        Note:
            This DOES update the data for other scores. Only perform this
                function IF you are absolutely certain that this score is
                going to be added to the database.
        """

    async def submit(self, clear_lbs: bool = True, calc_completed: bool = True) -> None:
        """Inserts the score into the database.
        
        Args:
            clear_lbs (bool): If true, the leaderboard and personal best
                cache for this beatmap + c_mode + mode combo.
        """

        if calc_completed: await self.calc_completed()
        if clear_lbs:
            caches.clear_lbs(self.bmap.md5, self.mode, self.c_mode)
            caches.clear_pbs(self.bmap.md5, self.mode, self.c_mode)

        table = self.c_mode.db_table
