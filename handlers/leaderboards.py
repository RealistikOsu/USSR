# TODO: Cleanup this mess.
from libs.time import Timer
from logger import info, debug
from typing import Optional
from objects.beatmap import Beatmap
from objects.leaderboard import GlobalLeaderboard, USER_ID_IDX, USERNAME_IDX
from globs import caches
from lenhttp import Request
from helpers.user import safe_name, fetch_user_country, edit_user
from consts.actions import Actions
from consts.mods import Mods
from consts.modes import Mode
from consts.c_modes import CustomModes
from consts.privileges import Privileges
from consts.complete import Completed
from consts.statuses import FetchStatus, LeaderboardTypes, Status
from globs.conn import sql
from libs.crypt import validate_md5

# Maybe make constants?
BASIC_ERR = b"error: no"
PASS_ERR = b"error: pass"

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

    name = score[USERNAME_IDX]
    if get_clans:
        clan = caches.clan.get(score[USER_ID_IDX])
        if clan: name = f"[{clan}] " + name

    return (f"{score[0]}|{name}|{round(score[1])}|{score[2]}|{score[3]}|"
            f"{score[4]}|{score[5]}|{score[6]}|{score[7]}|{score[8]}|"
            f"{score[9]}|{score[10]}|{score[13]}|{place}|{score[11]}|1")

def __log_not_served(md5: str, reason: str) -> None:
    """Prints a log into console about the leaderboard not being served.
    Args:
        md5 (str): The md5 has of the beatmap.
        reason (str): The reason why the leaderboard was not served.
    """

    info(f"Leaderboard for MD5 {md5} could not be served ({reason})")

async def leaderboard_get_handler(req: Request) -> None:
    """Handles beatmap leaderboards."""

    t = Timer().start()

    # Handle authentication.
    username = req.get_args["us"]
    safe_username = safe_name(username)
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
    c_mode = CustomModes.from_mods(mods, mode)

    # Simple checks to catch out cheaters and tripwires.
    if not validate_md5(md5): return BASIC_ERR
    if s_ver != 4:
        # Restrict them for outdated client.
        await edit_user(Actions.RESTRICT, user_id, "Bypassing client version protections.")
        return BASIC_ERR

    # Check if we can avoid any lookups.
    if md5 in caches.no_check_md5s:
        __log_not_served(md5, "Known Non-Existent Map")
        return __status_header(caches.no_check_md5s[md5])

    # Fetch leaderboards.
    # TODO: Other leaderboard types.
    lb = await GlobalLeaderboard.from_md5(md5, c_mode, mode)
    if not lb:
        caches.add_nocheck_md5(md5, Status.NOT_SUBMITTED)
        __log_not_served(md5, "No leaderboard/beatmap found")
        return __status_header(Status.NOT_SUBMITTED)

    # Personal best calculation.
    pb = None
    pb_pos = 0
    pb_fetch = FetchStatus.NONE
    if lb.user_has_score(user_id):
        # Check if we can just grab it from lb top.
        if lb.user_in_top(user_id):
            pb = lb.get_user_score(user_id)
            pb_pos = lb.get_user_placement(user_id)
            pb_fetch = FetchStatus.LOCAL
        else:
            # TODO: MySQL and caching of pb.
            print("MySQL")
            ...
    

    # Build Response.
    res = "\n".join([
        __beatmap_header(lb.bmap, lb.total_scores),
        "" if not pb else __format_score(pb, pb_pos, False),
        "\n".join(__format_score(score, idx + 1) for idx, score in enumerate(lb.scores))
    ])

    info(f"Beatmap {lb.bmap_fetch.console_text} / Leaderboard {lb.lb_fetch.console_text} / "
         f"PB {pb_fetch.console_text} | Served the {lb.c_mode.name} leaderboard for "
         f"{lb.bmap.song_name} to {username} in {t.time_str()}")
    return res
   