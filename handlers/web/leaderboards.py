# TODO: Cleanup this mess.
from libs.time import Timer
from logger import error, info, debug
from objects.beatmap import Beatmap
from objects.leaderboard import (
    GlobalLeaderboard,
    CountryLeaderboard,
    FriendLeaderboard,
    ModLeaderboard,
    USER_ID_IDX,
    USERNAME_IDX,
)
from globals import caches
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
from helpers.user import safe_name, edit_user
from constants.actions import Actions
from constants.mods import Mods
from constants.modes import Mode
from constants.c_modes import CustomModes
from constants.statuses import LeaderboardTypes, Status
from libs.crypt import validate_md5

# Maybe make constants?
BASIC_ERR = "error: no"
PASS_ERR = "error: pass"


def _status_header(st: Status) -> str:
    """Returns a beatmap header featuring only the status."""

    return f"{st.value}|false"


def _beatmap_header(bmap: Beatmap, score_count: int = 0) -> str:
    """Creates a response header for a beatmap."""

    if not bmap.has_leaderboard:
        return _status_header(bmap.status)

    return (
        f"{bmap.status.value}|false|{bmap.id}|{bmap.set_id}|{score_count}|0||\n"
        f"0\n{bmap.song_name}\n{bmap.rating}"
    )


def _format_score(score: tuple, place: int, get_clans: bool = True) -> str:
    """Formats a Database score tuple into a string format understood by the
    client."""

    name = score[USERNAME_IDX]
    if get_clans:
        clan = caches.clan.get(score[USER_ID_IDX])
        if clan:
            name = f"[{clan}] " + name

    return (
        f"{score[0]}|{name}|{round(score[1])}|{score[2]}|{score[3]}|"
        f"{score[4]}|{score[5]}|{score[6]}|{score[7]}|{score[8]}|"
        f"{score[9]}|{score[10]}|{score[13]}|{place}|{score[11]}|1"
    )


def _log_not_served(md5: str, reason: str) -> None:
    """Prints a log into console about the leaderboard not being served.
    Args:
        md5 (str): The md5 has of the beatmap.
        reason (str): The reason why the leaderboard was not served.
    """

    info(f"Leaderboard for MD5 {md5} could not be served ({reason})")


def error_score(msg: str) -> str:
    """Generates an error message as a score from the server bot."""

    return f"999|{msg}|999999999|0|0|0|0|0|0|0|0|0|999|0|0|1"


def error_lbs(msg: str) -> str:
    """Displays an error to the user in a visual manner."""

    return f"2|false\n\n\n\n\n" + "\n".join(
        [error_score("Leaderboard Error!"), error_score(msg)]
    )

async def leaderboard_get_handler(req: Request) -> Response:
    """Handles beatmap leaderboards."""

    t = Timer().start()

    # Handle authentication.
    username = req.query_params["us"]
    safe_username = safe_name(username)
    user_id = await caches.name.id_from_safe(safe_username)

    if not await caches.password.check_password(user_id, req.query_params["ha"]):
        debug(f"{username} failed to authenticate!")
        return PlainTextResponse(PASS_ERR)

    # Grab request args.
    md5 = req.query_params["c"]
    mods = Mods(int(req.query_params["mods"]))
    mode = Mode(int(req.query_params["m"]))
    s_ver = int(req.query_params["vv"])
    lb_filter = LeaderboardTypes(int(req.query_params["v"]))
    set_id = int(req.query_params["i"])
    c_mode = CustomModes.from_mods(mods, mode)

    # Simple checks to catch out cheaters and tripwires.
    if not validate_md5(md5):
        return PlainTextResponse(BASIC_ERR)

    if s_ver != 4:
        # Restrict them for outdated client.
        await edit_user(Actions.RESTRICT, user_id, "Bypassing client version protections.")

    # Check if we can avoid any lookups.
    if md5 in caches.no_check_md5s:
        _log_not_served(md5, "Known Non-Existent Map")
        return PlainTextResponse(_status_header(caches.no_check_md5s[md5]))

    # Fetch leaderboards.
    if lb_filter is LeaderboardTypes.GLOBAL:
        lb = await GlobalLeaderboard.from_md5(md5, c_mode, mode)
    elif lb_filter is LeaderboardTypes.COUNTRY:
        lb = await CountryLeaderboard.from_db(md5, c_mode, mode, user_id)
    elif lb_filter is LeaderboardTypes.FRIENDS:
        lb = await FriendLeaderboard.from_db(md5, c_mode, mode, user_id)
    elif lb_filter is LeaderboardTypes.MOD:
        lb = await ModLeaderboard.from_db(md5, c_mode, mode, mods.value)
    else:
        error(
            f"{username} ({user_id}) requested an unimplemented leaderboard type {lb_filter!r}!"
        )
        return PlainTextResponse(error_lbs("Unimplemented leaderboard type!"))

    if not lb:
        caches.add_nocheck_md5(md5, Status.NOT_SUBMITTED)
        _log_not_served(md5, "No leaderboard/beatmap found")
        return PlainTextResponse(_status_header(Status.NOT_SUBMITTED))

    # Personal best calculation.
    pb_fetch, pb_res = await lb.get_user_pb(user_id)

    # Build Response.
    res = "\n".join(
        [
            _beatmap_header(lb.bmap, lb.total_scores),
            "" if not pb_res else _format_score(pb_res.score, pb_res.placement, False),
            "\n".join(
                _format_score(score, idx + 1, score[USER_ID_IDX] != user_id)
                for idx, score in enumerate(lb.scores)
            ),
        ]
    )

    info(
        f"Beatmap {lb.bmap_fetch.console_text} / Leaderboard {lb.lb_fetch.console_text} / "
        f"PB {pb_fetch.console_text} | Served the {lb.c_mode.name} leaderboard for "
        f"{lb.bmap.song_name} to {username} in {t.time_str()}"
    )
    return PlainTextResponse(res)
