from logger import info, debug
from typing import Optional
from objects.beatmap import Beatmap
from globs import caches
from lenhttp import Request
from helpers.user import safe_name, fetch_user_country
from consts.mods import Mods
from consts.modes import Mode
from consts.c_modes import CustomModes
from consts.privileges import Privileges
from consts.complete import Completed
from consts.statuses import LeaderboardTypes, Status
from globs.conn import sql
from libs.crypt import validate_md5

# Maybe make constants?
BASIC_ERR = b"error: no"
PASS_ERR = b"error: pass"
SCORE_LIMIT = 100

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
WHERE
    {where_clauses}
ORDER BY {order} DESC
LIMIT {limit}
"""

COUNT_QUERY = ("SELECT COUNT(*) FROM {table} s INNER JOIN users a on "
               "s.userid = a.id WHERE {where_clauses}")

PB_BASE_QUERY = """
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
WHERE
    {where_clauses}
ORDER BY {order} DESC
LIMIT 1
"""

PB_COUNT_QUERY = """
SELECT
    COUNT(*) + 1
FROM
    {table} s
INNER JOIN
    users a on s.userid = a.id
WHERE
    {where_clauses}
ORDER BY {order} DESC
"""

async def __fetch_global(bmap: Beatmap, mode: Mode, c_mode: CustomModes) -> tuple:
    """Fetches the global leaderboards for a given beatmap, returning the
    results tuple directly. Also returns the amount of scores."""

    # Consult our cache first.
    cache = caches.get_lb_cache(mode, c_mode)
    cached_lbs = cache.get(bmap.md5)

    if not cached_lbs:
        scoring = "pp" if c_mode.uses_ppboard else "score"
        table = "scores" + c_mode.to_db_suffix()

        # SQL Query Generation.
        where_clauses = (
            f"a.privileges & {Privileges.USER_PUBLIC.value}",
            "s.beatmap_md5 = %s",
            "s.play_mode = %s",
            f"s.completed = {Completed.BEST.value}",
        )
        where_args = (
            bmap.md5,
            mode.value,
        )
        where_str = " AND ".join(where_clauses)

        query = BASE_QUERY.format(
            scoring= scoring,
            table= table,
            where_clauses= where_str,
            limit= SCORE_LIMIT,
            order= "pp" if c_mode.uses_ppboard else "score",
        )

        scores_db = await sql.fetchall(query, where_args)

        # Calculating score amount.
        score_count = len(scores_db)
        if score_count == SCORE_LIMIT:
            # There are more scores. Consult the database.
            score_count = await sql.fetchcol(
                COUNT_QUERY.format(table= table, where_clauses= where_str),
                where_args
            )
        
        # Cache lbs for later.
        cache.cache(bmap.md5, (scores_db, score_count))
    else:
        scores_db, score_count = cached_lbs

    return scores_db, score_count

async def __fetch_pb(bmap: Beatmap, mode: Mode, c_mode: CustomModes,
                     user_id: int, scores: tuple = ()) -> tuple:
    """Fetches a user's personal best for a given beatmap, returning the
    result tuple directly. Also returns the score's position on the global leaderboards."""

    # Consult our cache first.
    cache = caches.get_pb_cache(mode, c_mode)
    cached_pb = cache.get((user_id, bmap.md5))

    if not cached_pb:
        # Check if we can get our score from scores.
        score_iter_data = __score_from_data(scores, user_id)
        # We gotta consult the db.
        if not score_iter_data[1] is not None:
            scoring = "pp" if c_mode.uses_ppboard else "score"
            table = "scores" + c_mode.to_db_suffix()

            # SQL Query Generation.
            where_clauses = (
                f"a.privileges & {Privileges.USER_PUBLIC.value}",
                "s.beatmap_md5 = %s",
                "s.play_mode = %s",
                f"s.completed = {Completed.BEST.value}",
                "a.id = %s",
            )
            where_args = (
                bmap.md5,
                mode.value,
                user_id,
            )
            where_str = " AND ".join(where_clauses)

            query = PB_BASE_QUERY.format(
                scoring= scoring,
                table= table,
                where_clauses= where_str,
                order= "pp" if c_mode.uses_ppboard else "score",
            )

            personal_best = await sql.fetchone(query, where_args)

            if not personal_best:
                personal_best = None # osu! client still expects an empty string for personal bests
                personal_place = None
            else: # TODO: Query const to merge score & count query into one?
                place_where_clauses = (
                    f"a.privileges & {Privileges.USER_PUBLIC.value}",
                    "s.beatmap_md5 = %s",
                    "s.play_mode = %s",
                    f"s.pp > {personal_best[14]}",
                    f"s.completed = {Completed.BEST.value}",
                )
                place_where_str = " AND ".join(place_where_clauses)

                query = PB_COUNT_QUERY.format(
                    table= table,
                    where_clauses= place_where_str,
                    order= "pp" if c_mode.uses_ppboard else "score",
                )

                # Here we dont use ID arg.
                where_args = where_args[:2]

                personal_place = await sql.fetchcol(query, where_args)

        # We can unpack.
        else:
            personal_best, personal_place = score_iter_data

        # Cache personal best for later.
        cache.cache((user_id, bmap.md5), (personal_best, personal_place))
    else:
        personal_best, personal_place = cached_pb

    return personal_best, personal_place

async def __fetch_country(bmap: Beatmap, mode: Mode,
                          c_mode: CustomModes, country: str) -> tuple[tuple]:
    """Fetches the leaderboards for a given country. Pure MySQL due to"""

    # SQL Query Generation.
    where_clauses = (
        f"a.privileges & {Privileges.USER_PUBLIC.value}",
        "s.beatmap_md5 = %s",
        "s.play_mode = %s",
        f"s.completed = {Completed.BEST.value}",
        "a.country = %s",
    )
    where_args = (
        bmap.md5,
        mode.value,
        country,
    )
    where_str = " AND ".join(where_clauses)

    query = BASE_QUERY.format(
        table= c_mode.db_table,
        order= "pp" if c_mode.uses_ppboard else "score",
        where= where_str
    )

    scores_db = await sql.fetchall(query, where_args)

    # Check if we can use this as len.
    scores_count = len(scores_db)

    if scores_count == SCORE_LIMIT:
        scores_count= await sql.fetchcol(
            COUNT_QUERY.format(
                where= where_str,
                table= c_mode.db_table
            ), where_args
        )

    return scores_db, scores_count

async def __fetch_country_pb(bmap: Beatmap, mode: Mode,
                          c_mode: CustomModes, country: str,
                          user_id: int, scores: tuple[tuple]) -> tuple[tuple, int]:
    """Fetches the personal best for a given sountry lb."""

    # TODO: Proper SQL.
    return __score_from_data(scores, user_id)

def __status_header(st: Status) -> str:
    """Returns a beatmap header featuring only the status."""

    return f"{st.value}|false"

def __beatmap_header(bmap: Beatmap, score_count: int = 0) -> str:
    """Creates a response header for a beatmap."""

    if not bmap.has_leaderboard:
        return __status_header(bmap.status)
    
    return (f"{bmap.status.value}|false|{bmap.id}|{bmap.set_id}|{score_count}\n"
            f"0\n{bmap.song_name}\n{bmap.rating}")

def __format_score(score: tuple, place: int, get_clans: bool = True) -> str:
    """Formats a Database score tuple into a string format understood by the
    client."""

    name = score[12]
    if get_clans:
        clan = caches.clan.get(score[13])
        if clan:
            name = f"[{clan}] " + name

    return (f"{score[0]}|{name}|{round(score[1])}|{score[2]}|{score[3]}|"
            f"{score[4]}|{score[5]}|{score[6]}|{score[7]}|{score[8]}|"
            f"{score[9]}|{score[10]}|{score[13]}|{place}|{score[11]}|1")
    
def __score_from_data(scores: tuple, user_id: int,
                      lb_size: int = SCORE_LIMIT) -> Optional[tuple[int, tuple]]:
    """Iterates over a tuple of scores (SQL format) and locates a score and
    place on the leaderboard. Big optimisation.
    
    Note:
        If position = 0, score is 100% not in the lb. If none, sql query has
            to be ran to lookup.
    """

    for idx, score in enumerate(scores):
        # Score of our user is found.
        if score[13] == user_id:
            return score, idx + 1
    
    # Ok now this is 500iq move. If the amount of total scores is below the
    # limit and did not appear prior, we know it doesn't exist.
    if len(scores) < lb_size: return None, 0
    return None, None

async def leaderboard_get_handler(req: Request) -> None:
    """Handles beatmap leaderboards."""

    # Handle authentication.
    safe_username = safe_name(req.get_args["us"])
    user_id = await caches.name.id_from_safe(safe_username)

    if not await caches.password.check_password(user_id, req.get_args["ha"]):
        return PASS_ERR
    
    # Grab request args.
    md5 = req.get_args["c"]
    mods = Mods(int(req.get_args["mods"]))
    mode = Mode(int(req.get_args["m"]))
    s_ver = int(req.get_args["vv"])
    b_filter = LeaderboardTypes(int(req.get_args["v"]))
    set_id = int(req.get_args["i"])
    c_mode = CustomModes.from_mods(mods)

    # Simple checks to catch out cheaters and tripwires. TODO: mb restrict?
    if not validate_md5(md5): return BASIC_ERR
    if s_ver != 4: return BASIC_ERR

    # Check if we can avoid any lookups.
    if md5 in caches.no_check_md5s:
        return __status_header(caches.no_check_md5s[md5])

    # Fetch beatmap object.
    beatmap = await Beatmap.from_md5(md5)

    # Fetch scores and generate response.
    if not beatmap:
        # TODO: Handle beatmap updates.
        debug(f"Beatmap not found for MD5 {md5}")
        ...

        # If set doesn't exist, we cache current map as unavailable.
        caches.add_nocheck_md5(md5, Status.UNAVAILABLE)
        return BASIC_ERR

    if beatmap.deserves_update:
        updated = await beatmap.try_update()
        # They need to update the beatmap.
        if updated:
            return __status_header(Status.UPDATE_AVAILABLE)
    
    if not beatmap.has_leaderboard:
        # Just the header is required here.
        debug(f"Beatmap status {beatmap.status!r} does not offer leaderboards!")
        return __beatmap_header(beatmap)
    
    # Leaderboard types.
    if b_filter == LeaderboardTypes.TOP:
        scores_db, score_count = await __fetch_global(
            beatmap,
            mode,
            c_mode,
        )

        personal_best, personal_place = await __fetch_pb(
            beatmap,
            mode,
            c_mode,
            user_id,
            scores_db,
        )
    
    elif b_filter == LeaderboardTypes.COUNTRY:
        country = await fetch_user_country(user_id)
        scores_db, score_count = await __fetch_country(
            beatmap,
            mode,
            c_mode,
            country,
        )

        personal_best, personal_place = await __fetch_country_pb(
            beatmap,
            mode,
            c_mode,
            user_id,
            scores_db,
        )
    
    else:
        debug(f"Requested unhandled leaderboard type! ({b_filter!r})")
        return BASIC_ERR

    result = "\n".join((
        __beatmap_header(beatmap, score_count),
        __format_score(personal_best, personal_place, False) if personal_place else "",
        *[__format_score(s, idx + 1) for idx, s in enumerate(scores_db)]
    ))

    info(f"Served leaderboards for {beatmap.song_name}!")
    
    return result
