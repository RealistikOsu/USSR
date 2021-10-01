from dataclasses import dataclass
from libs.time import get_timestamp
from typing import Optional
from consts.modes import Mode
from consts.statuses import Status
from globs.caches import beatmaps
from globs.conn import sql
from logger import debug, error
from conn.web_client import simple_get_json
from config import conf

@dataclass
class Beatmap:
    """An object representing an osu! beatmap."""

    id: int = 0
    set_id: int = 0
    md5: str = ""
    # I personally would store separately but ripple db
    song_name: str = ""
    ar: float = 0.0
    od: float = 0.0
    mode: Mode = Mode(0)
    max_combo: Optional[int] = 0 # The osu API does not sometimes send this.
    hit_length: int = 0
    bpm: int = 0
    rating: int = 10
    playcount: int = 0
    passcount: int = 0
    last_update: int = 0
    status: Status = Status(0)
    status_frozen: bool = False
    # Ripple schema difficulties
    difficulty_std: float = 0.0
    difficulty_taiko: float = 0.0
    difficulty_ctb: float = 0.0
    difficulty_mania: float = 0.0

    ## PROPERTIES
    @property
    def difficulty(self) -> float:
        """Returns the star difficulty for the beatmap's main mode."""

        return self.__getattribute__(_diff_attribs[self.mode.value])
    
    @property
    def has_leaderboard(self) -> bool:
        """Bool corresponding to whether the beatmap features a leaderboard."""

        return self.status.value in _leaderboard_statuses
    
    ## CLASSMETHODS
    @classmethod
    async def from_oapi_v1(cls, md5: str) -> Optional['Beatmap']:
        """Attempts to create an instance of `Beatmap` using data fetched from
        the osu!api v1.

        Note:
            This is a slow function call due to creating a GET request to
                an external API.
            This function does not consider rate limits imposed by the osu API.
                Use with care.
        
        Args:
            md5 (str): The MD5 hash of the `.osu` beatmap file.

        Returns:
            Instance of `Beatmap` on successful fetch. Else `None`.
        """

        debug(f"Starting osu!api v1 fetch of beatmap {md5}")
        try:
            found_beatmaps = await simple_get_json(
                "https://old.ppy.sh/api/get_beatmaps", {
                    "k": conf.osu_api_key,
                    "h": md5
                }
            )
        except Exception: return error("Failed to fetch map from the osu!api")
        if not found_beatmaps:
            return debug(f"Beatmap {md5} not found in the api.")
        
        map_json, = found_beatmaps
        song_name = _create_full_name(
            artist= map_json["artist"],
            title= map_json["title"],
            difficulty= map_json["version"]
        )
        max_combo = int(mc) if (mc := map_json["max_combo"]) else None

        # We now create the object with the data.
        # NOTE: All values sent by oapi v1 are strings.
        bmap = Beatmap(
            id= int(map_json["beatmap_id"]),
            set_id= int(map_json["beatmapset_id"]),
            md5= md5,
            song_name= song_name,
            ar= float(map_json["diff_approach"]),
            od= float(map_json["diff_overall"]),
            mode= Mode(int(map_json["mode"])), # You may not have to int it.
            max_combo= max_combo,
            hit_length= int(map_json["hit_length"]),
            bpm= round(float(map_json["bpm"])),
            last_update= get_timestamp()
        )
        # Set star diff for the main mode.
        bmap.__setattr__(
            _diff_attribs[bmap.mode.value],
            round(float(map_json["difficultyrating"]), 2)
        )

        return bmap
    
    @classmethod
    async def from_db(self, md5: str) -> Optional['Beatmap']:
        """Fetches data from MySQL and creates an instance of `Beatmap` from it.
        
        Args:
            md5 (str): The MD5 hash of the `.osu` beatmap file.

        Returns:
            Instance of `Beatmap` on successful fetch. Else `None`.
        """

        # This query is not very fun...
        map_db = await sql.fetchone(
            "SELECT beatmap_id, beatmapset_id, beatmap_md5, song_name, ar, od, "
            "mode, rating, difficulty_std, difficulty_taiko, difficulty_ctb, "
            "difficulty_mania, max_combo, hit_length, bpm, playcount, passcount, "
            "ranked, latest_update, ranked_status_freezed FROM beatmaps WHERE "
            "beatmap_md5 = %s LIMIT 1", (md5,)
        )

        # Not found check.
        if not map_db: return

        return Beatmap(
            id= map_db[0],
            set_id= map_db[1],
            md5= map_db[2],
            song_name= map_db[3],
            ar= map_db[4],
            od= map_db[5],
            mode= Mode(map_db[6]),
            rating= map_db[7],
            difficulty_std= map_db[8],
            difficulty_taiko= map_db[9],
            difficulty_ctb= map_db[10],
            difficulty_mania= map_db[11],
            max_combo= map_db[12],
            hit_length= map_db[13],
            bpm= map_db[14],
            playcount= map_db[15],
            passcount= map_db[16],
            status= Status(map_db[17]),
            last_update= int(map_db[18]),
            status_frozen= not not map_db[19]
        )
    
    @classmethod
    async def from_cache(self, md5: str) -> Optional['Beatmap']:
        """Tries to fetch an existing instance of `Beatmap` from the global
        Beatmap cache.
        
        Args:
            md5 (str): The MD5 hash of the `.osu` beatmap file.

        Returns:
            Instance of `Beatmap` on successful fetch. Else `None`.
        """

        beatmaps.get(md5)
    
    @classmethod
    async def from_md5(_, md5: str)  -> Optional['Beatmap']:
        """Attempts to create/fetch an instance of beatmap using multiple
        sources ordered by speed. High level API.
        
        Note:
            The order of sources is: Cache, MySQL, oapiv1.

        Args:
            md5 (str): The MD5 hash of the `.osu` beatmap file.

        Returns:
            Instance of `Beatmap` on successful fetch. Else `None`.
        """

        for fetch in _fetch_order:
            res = await fetch(md5)
            # We have our map.
            if res:
                # Check if we used a fetch that lets us cache.
                if fetch in _cachable: res.cache()
                if fetch in _insertable: await res.insert_db()
                return res
    
    def cache(self) -> None:
        """Caches the beatmap to the global beatmap cache.
        
        Note:
            Raises `ValueError` if the beatmap id is equal to 0.
        """

        if not self.id: raise ValueError(
            "Unloaded beatmaps (id = 0) may not be cached!"
        )
        beatmaps.cache(self.md5, self)
    
    async def delete_db(self) -> None:
        """Deletes all instances of the beatmap from the database.
        
        Note:
            This does NOT nuke the set.
        """

        await sql.execute(
            "DELETE FROM beatmaps WHERE beatmap_id = %s", (self.id,)
        )
    
    async def insert_db(self, bypass_exist_check: bool = False) -> None:
        """Inserts the beatmap into the MySQL database.
        
        Args:
            bypass_exist_check (bool): If true, the check to make sure that
                the beatmap is not already in the database will not be
                performed.
        """

        await sql.execute(
            "INSERT INTO `beatmaps` (`beatmap_id`, `beatmapset_id`, "
            "`beatmap_md5`, `song_name`, `ar`, `od`, `mode`, `rating`, "
            "`difficulty_std`, `difficulty_taiko`, `difficulty_ctb`, "
            "`difficulty_mania`, `max_combo`, `hit_length`, `bpm`, `playcount`, "
            "`passcount`, `ranked`, `latest_update`, `ranked_status_freezed`) VALUES " #21
            "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                self.id,
                self.set_id,
                self.md5,
                self.song_name,
                self.ar,
                self.od,
                self.mode.value,
                self.rating,
                self.difficulty_std,
                self.difficulty_taiko,
                self.difficulty_ctb,
                self.difficulty_mania,
                self.max_combo,
                self.hit_length,
                self.bpm,
                self.playcount,
                self.passcount,
                self.status.value,
                self.last_update,
                int(self.status_frozen)
            )
        )
    
    async def increment_playcount(self, passcount: bool = True) -> None:
        """Increments the beatmap playcount for the object and MySQL.
        
        Args:
            passcount (bool): Whether the beatmap passcount should also be
                incremented.
        """

        self.playcount += 1
        if passcount: self.passcount += 1

        await sql.execute(
            "UPDATE beatmaps SET passcount = %s, playcount = %s WHERE "
            "beatmap_md5 = %s LIMIT 1", (self.passcount, self.playcount)
        )

_diff_attribs = {
    Mode.STANDARD: "difficulty_std",
    Mode.TAIKO:    "difficulty_taiko",
    Mode.CATCH:    "difficulty_ctb",
    Mode.MANIA:    "difficulty_mania"
}

_fetch_order = (
    Beatmap.from_cache,
    Beatmap.from_db,
    Beatmap.from_oapi_v1,
)
_cachable = ( # Funcs that should be cached.
    Beatmap.from_db,
    Beatmap.from_oapi_v1,
)

_insertable = ( # Funcs that should be inserted into the db
    Beatmap.from_oapi_v1,
)

_leaderboard_statuses = (
    Status.RANKED,
    Status.LOVED,
    Status.APPROVED,
    Status.QUALIFIED
)

def _create_full_name(artist: str, title: str, difficulty: str) -> str:
    """Creates a full name out of song details for storage in the database."""

    return f"{artist} - {title} [{difficulty}]"
