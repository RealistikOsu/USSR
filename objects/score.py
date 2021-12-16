from dataclasses import dataclass
from helpers.discord import log_first_place
from helpers.pep import announce
from helpers.user import safe_name
from typing import Optional
from logger import debug, error, warning
from consts.modes import Mode
from consts.mods import Mods
from consts.c_modes import CustomModes
from consts.complete import Completed
from consts.privileges import Privileges
from objects.beatmap import Beatmap
from globs.conn import sql
from globs import caches
from libs.crypt import validate_md5
from libs.time import get_timestamp
from lenhttp import Request
from py3rijndael import RijndaelCbc, ZeroPadding
from config import conf
from .leaderboard import GlobalLeaderboard
import base64
import traceback

# PP Calculators
from pp.main import select_calculator

FETCH_SCORE = """
SELECT
    s.id,
    s.beatmap_md5,
    s.userid,
    s.score,
    s.max_combo,
    s.full_combo,
    s.mods,
    s.300_count,
    s.100_count,
    s.50_count,
    s.katus_count,
    s.gekis_count,
    s.misses_count,
    s.time,
    s.play_mode,
    s.completed,
    s.accuracy,
    s.pp,
    s.playtime,
    a.username
FROM {table} s
INNER JOIN users a ON s.userid = a.id
WHERE {cond}
LIMIT {limit}
"""

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
    sr: float
    username: str

    @property
    def is_submitted(self) -> bool:
        """Bool corresponding to whether the score has been submitted."""

        return self.id != 0
    
    @classmethod
    async def from_score_sub(self, req: Request) -> Optional['Score']:
        """Creates an instance of `Score` from data provided in a score
        submit request."""

        aes = RijndaelCbc(
            key= "osu!-scoreburgr---------" + req.post_args["osuver"],
            iv= base64.b64decode(req.post_args["iv"]).decode("latin_1"),
            padding= ZeroPadding(32),
            block_size= 32,
        )
        score_data = aes.decrypt(
            base64.b64decode(req.post_args["score"]).decode("latin_1")
        ).decode().split(":")

        # Set data from the score sub.
        map_md5 = score_data[0]

        # Verify map.
        if not validate_md5(map_md5):
            warning(f"Score submit provided invalid beatmap md5 ({map_md5})! "
                    "Giving up.")
            return
        
        # Verify score data sent is correct.
        if len(score_data) != 18: # Not sure if we restrict for this
            warning(f"Someone sent over incorrect score data.... Giving up.")
            return
        
        username = score_data[1].rstrip()
        user_id = await caches.name.id_from_safe(safe_name(username))
        bmap = await Beatmap.from_md5(map_md5)
        mods = Mods(int(score_data[13]))
        mode = Mode(int(score_data[15]))

        s = Score(
            0, bmap, user_id,
            int(score_data[9]),
            int(score_data[10]),
            score_data[11] == "True",
            score_data[14] == "True",
            req.post_args.get("x") == "1",
            mods,
            CustomModes.from_mods(mods, mode),
            int(score_data[3]),
            int(score_data[4]),
            int(score_data[5]),
            int(score_data[7]),
            int(score_data[6]),
            int(score_data[8]),
            get_timestamp(),
            mode,
            None,
            0.0,
            0.0,
            0, # TODO: Playtime
            0,
            score_data[12],
            0.0,
            username
        )

        s.calc_accuracy()

        return s
    
    async def calc_completed(self) -> Completed:
        """Calculated the `complete` attribute for scores.
        
        Note:
            This DOES update the data for other scores. Only perform this
                function IF you are absolutely certain that this score is
                going to be added to the database.
            Running first place first is recommended for a potential perf
                save.
        """

        debug("Calculating completed.")

        # Get the simple ones out the way.
        if self.placement == 1:
            self.completed = Completed.BEST
            return self.completed
        elif self.quit:
            self.completed = Completed.QUIT
            return self.completed
        elif not self.passed:
            self.completed = Completed.FAILED
            return self.completed
        
        # Don't bother for non-lb things.
        if not self.bmap.has_leaderboard:
            self.completed = Completed.COMPLETE
            return self.completed
        
        table = self.c_mode.db_table
        scoring = "pp"
        val = self.pp

        debug("Using MySQL to calculate Completed.")

        query = (
            f"userid = %s AND completed = {Completed.BEST.value} AND beatmap_md5 = %s "
            f"AND play_mode = {self.mode.value}"
        )
        args = (self.user_id, self.bmap.md5,)
        
        # TODO: Set old best to mod best etc
        await sql.execute(
            f"UPDATE {table} SET completed = {Completed.COMPLETE.value} WHERE "
            + query + f" AND {scoring} < {val} LIMIT 1", args
        )

        # Check if it remains.
        ex_db = await sql.fetchcol(
            f"SELECT 1 FROM {table} WHERE " + query + " LIMIT 1",
            args
        )

        if not ex_db:
            self.completed = Completed.BEST
            return self.completed
        
      
        self.completed = Completed.COMPLETE
        return self.completed
        # TODO: Mod bests
    
    async def calc_placement(self) -> int:
        """Calculates the placement of the score on the leaderboards.
        
        Note:
            Performs a generally costly query.
            Returns 0 if bmap ranked status doesnt have lbs.
            Returns 0 if completed doesnt allow.
        """

        if (not self.passed) or (not self.bmap.has_leaderboard):
            debug("Not bothering calculating placement.")
            self.placement = 0
            return 0
        
        debug("Calculating score placement based on MySQL.")

        table = self.c_mode.db_table
        scoring = "pp" if self.c_mode.uses_ppboard else "score"
        val = self.pp if self.c_mode.uses_ppboard else self.score

        self.placement = (await sql.fetchcol(
            f"SELECT COUNT(*) FROM {table} s INNER JOIN users u ON s.userid = "
            f"u.id WHERE u.privileges & {Privileges.USER_PUBLIC.value} AND "
            f"s.play_mode = {self.mode.value} AND s.completed = {Completed.BEST.value} "
            f"AND {scoring} > %s AND s.beatmap_md5 = %s",
            (val, self.bmap.md5)
        )) + 1

        return self.placement
    
    async def calc_pp(self) -> float:
        """Calculates the PP given for the score."""

        if (not self.bmap.has_leaderboard):# or (not self.passed):
            debug("Not bothering to calculate PP.")
            self.pp = .0
            return self.pp
        debug("Calculating PP...") # We calc for failed scores!
        
        # TODO: More calculators (custom for standard.)
        calc = select_calculator(self.mode, self.c_mode).from_score(self)
        try: self.pp, self.sr = await calc.calculate()
        except Exception:
            error("Could not calculate PP for score! Setting to 0. Error: " + traceback.format_exc())
        return self.pp
    
    # This gives me aids looking at it LOL. Copied from old Kisumi
    def calc_accuracy(self) -> float:
        """Calculates the accuracy of the score. Credits to Ripple for this as
        osu! wiki is not working :woozy_face:"""

        acc = .0
        # osu!std
        if self.mode == Mode.STANDARD:
            acc =  (
                (self.count_50*50+self.count_100*100+self.count_300*300)
                / ((self.count_300+self.count_100+self.count_50+self.count_miss) * 300)
            )
        # These may be slightly inaccurate but its the best we have without some next gen calculations.
        # Taiko
        elif self.mode == Mode.TAIKO:
            acc = (
                (self.count_100*50)+(self.count_300*100))/(
                (
                    self.count_300+self.count_100+self.count_miss
                ) * 100
            )
        # Catch the beat
        elif self.mode == Mode.CATCH:
            acc = (
                (self.count_300+self.count_100+self.count_50)
                / (self.count_300+self.count_100+self.count_50+self.count_miss+self.count_katu)
            )
        # Mania
        elif self.mode == Mode.MANIA:
            acc = (
                (
                    self.count_50*50+self.count_100*100+self.count_katu*200+self.count_300*300+self.count_geki*300
                ) / (
                    (self.count_miss+self.count_50+self.count_100+self.count_300+self.count_geki+self.count_katu) * 300
                )
            )
        
        # I prefer having it as a percentage.
        self.accuracy = acc * 100
        return self.accuracy
    
    async def on_first_place(self) -> None:
        """Adds the score to the first_places table."""

        # Why did I design this system when i was stupid...

        # Delete previous first place.
        await sql.execute(
            "DELETE FROM first_places WHERE beatmap_md5 = %s AND mode = %s AND "
            "relax = %s LIMIT 1",
            (self.bmap.md5, self.mode.value, self.c_mode.value)
        )

        # And now we insert the new one.
        await sql.execute(
            "INSERT INTO first_places (score_id, user_id, score, max_combo, full_combo,"
            "mods, 300_count, 100_count, 50_count, miss_count, timestamp, mode, completed,"
            "accuracy, pp, play_time, beatmap_md5, relax) VALUES "
            "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (self.id, self.user_id, self.score, self.max_combo, self.full_combo,
            self.mods.value, self.count_300, self.count_100, self.count_50, self.count_miss,
            self.timestamp, self.mode.value, self.completed.value, self.accuracy, self.pp,
            self.play_time, self.bmap.md5, self.c_mode.value)
        )
        debug("First place added.")

        # TODO: Move somewhere else.
        msg = (f"[{self.c_mode.acronym}] User [{conf.srv_url}/u/{self.user_id} "
        f"{self.username}] has submitted a #1 place on "
        f"[{conf.srv_url}/beatmaps/{self.bmap.id} {self.bmap.song_name}]"
        f" +{self.mods.readable} ({round(self.pp, 2)}pp)")
        # Announce it.
        await announce(msg)
        await log_first_place(self)
    
    def insert_into_lb_cache(self) -> None:
        """Inserts the score into cached leaderboards if the leaderboards are
        already cached.
        
        Note:
            Only run if completed is equal to `Completed.BEST`. Else, it will
            lead to a weird state of the leaderboards, with wrong scores
            appearing.
        """

        lb = GlobalLeaderboard.from_cache(self.bmap.md5, self.c_mode, self.mode)
        if lb is not None: lb.insert_user_score(self)

    async def submit(self, clear_lbs: bool = True, calc_completed: bool = True,
                     calc_place: bool = True, calc_pp: bool = True,
                     restricted: bool = False) -> None:
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
            calc_pp (bool): Whether the PP for the score should be recalculated
                from scratch.
            restricted (bool): Whether the user is restricted or not. If true,
                `on_first_place` and `insert_into_lb_cache` will NOT be called
        """

        if calc_pp: await self.calc_pp() # We need this for the rest.
        if calc_completed: await self.calc_completed()
        if calc_place: await self.calc_placement()

        await self.__insert()

        # Handle first place.
        if self.placement == 1 and not restricted:
            await self.on_first_place()
        
        # Insert to cache after score ID is assigned.
        if clear_lbs and self.completed is Completed.BEST \
            and self.bmap.has_leaderboard and not restricted:
            self.insert_into_lb_cache()

    async def __insert(self) -> None:
        """Inserts the score directly into the database. Also assigns the
        `id` attribute to the score ID."""

        table = self.c_mode.db_table
        ts = get_timestamp()

        debug("Inserting score into the MySQL database.")

        self.id = await sql.execute(
            f"INSERT INTO {table} (beatmap_md5, userid, score, max_combo, full_combo, mods, "
            "300_count, 100_count, 50_count, katus_count, gekis_count, misses_count, time, "
            "play_mode, completed, accuracy, pp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"
            "%s,%s,%s,%s,%s)",
            (self.bmap.md5, self.user_id, self.score, self.max_combo, int(self.full_combo),
            self.mods.value, self.count_300, self.count_100, self.count_50, self.count_katu,
            self.count_geki, self.count_miss, ts, self.mode.value, self.completed.value,
            self.accuracy, self.pp)
        )
    
    async def save_pp(self) -> None:
        """Saves the score PP attribute to the scores table.
        
        Note:
            This does NOT raise an exception if score is not submitted.
        """

        await sql.execute(
            f"UPDATE {self.c_mode.db_table} SET pp = %s WHERE id = %s LIMIT 1",
            (self.pp, self.id)
        )
    
    @classmethod
    async def from_tuple(cls, tup: tuple, bmap: Optional[Beatmap] = None) -> 'Score':
        """Creates an instance of `Score` form a tuple straight from MySQL.
        
        Format:
            The tuple must feature the following arguments in the specific order:
            id, beatmap_md5, userid, score, max_combo, full_combo, mods, 300_count,
            100_count, 50_count, katus_count, gekis_count, misses_count, timestamp,
            play_mode, completed, accuracy, pp, playtime, username.
        
        Args:
            tup (tuple): The tuple to create the score from.
            bmap (Beatmap, optional): The beatmap to use. If not provided, will be
                manually fetched.
        
        Returns:
            Score: The score object.
        """

        completed = Completed(tup[15])
        passed = completed.completed
        quit = completed == Completed.QUIT
        bmap = bmap or await Beatmap.from_md5(tup[1])
        mods = Mods(tup[6])
        mode = Mode(tup[14])
        c_mode = CustomModes.from_mods(mods, mode)

        return Score(
            id= tup[0],
            bmap= bmap,
            user_id= tup[2],
            score= tup[3],
            max_combo= tup[4],
            full_combo= bool(tup[5]),
            mods= mods,
            count_300= tup[7],
            count_100= tup[8],
            count_50= tup[9],
            count_katu= tup[10],
            count_geki= tup[11],
            count_miss= tup[12],
            timestamp= int(tup[13]),
            mode= mode,
            completed= completed,
            accuracy= tup[16],
            pp= tup[17],
            play_time= tup[18],
            username= tup[19],
            passed= passed,
            quit= quit,
            c_mode= c_mode,
            placement= 0,
            sr= 0.0,
            grade= "X",
        )

    @classmethod
    async def from_db(cls, score_id: int, c_mode: CustomModes,
                      calc_placement: bool = True) -> Optional['Score']:
        """Creates an instance of `Score` using data fetched from the
        database.
        
        Args:
            score_id (int): The ID of the score within the database.
            table (str): The table the score should be loacted within 
                (directly formatted into the query).
            calc_placement (bool): Whether the placement of the score should be
                calculated.
        """

        table = c_mode.db_table
        s_db = await sql.fetchone(
            FETCH_SCORE.format(
                table= table,
                cond= "s.id = %s",
                limit= "1",
            ), (score_id,)
        )

        if not s_db: return
        s = await cls.from_tuple(s_db)
       
        if calc_placement: await s.calc_placement()

        return s
    
    def as_score_tuple(self, pp_board: bool) -> tuple[object, ...]:
        """Converts the score object to a tuple used within the leaderboard
        caching system.
        
        Format:
            The tuple has objects in the following order:
            id, <scoring>, max_combo, 50_count, 100_count, 300_count, misses_count,
            katus_count, gekis_count, full_combo, mods, time, username, user_id, pp
        """

        scoring = self.pp if pp_board else self.score

        return (
            self.id, scoring, self.max_combo, self.count_50, self.count_100,
            self.count_300, self.count_miss, self.count_katu, self.count_geki,
            int(self.full_combo), self.mods.value, self.timestamp, self.username,
            self.user_id, self.pp
        )
