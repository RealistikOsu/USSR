from __future__ import annotations

import logging
import time

from fastapi import Depends
from fastapi import Query
from fastapi import Response

import app.state
import app.usecases
from app.constants.lastfm import LastFMFlags
from app.models.user import User
from app.usecases.user import authenticate_user

# Down to earth explanations for each flag to be understandable to
# the average admin.
_flag_expl = {
    LastFMFlags.TIMEWARP: "[LIKELY] Timewarp flag triggered (audio is desynced from expected position)! "
    "May be caused by lag on the user's end.",
    LastFMFlags.INCORRECT_MOD_VALUE: "[MIXED] The score's mod value didn't match enabled mods (possible "
    "sign of a mod remover such as Hidden remover).",
    LastFMFlags.MULTIPLE_OSU_CLIENTS: "[MIXED] The user had multiple instances of osu! open.",
    LastFMFlags.CHECKSUM_FAIL: "[LIKELY] The score related memory has been edited in a weird manner.",
    LastFMFlags.FLASHLIGHT_CHECKSUM_FAIL: "[UNKNOWN] FL Checksum fail occurence is unknown.",
    LastFMFlags.FLASHLIGHT_REMOVER: "[CERTAIN] User is using a flashlight remover.",
    LastFMFlags.WINDOW_OVERLAY: "[LIKELY] A transparent window is overlaying the osu! client.",
    LastFMFlags.FAST_PRESS: "[LIKELY] User is consistently hitting notes with a low latency in mania.",
    LastFMFlags.MOUSE_DISCREPENCY: "[LIKELY] Something is altering the mouse position the mouse info "
    "on the position received by the game.",
    LastFMFlags.KB_DISCREPENCY: "[LIKELY] Something is altering the keyboard presses received by the game.",
    LastFMFlags.LF_FLAG_PRESENT: "[UNKNOW] LF flag is present. Occurence of this is unknown.",
    LastFMFlags.OSU_DEBUGGED: "[LIKELY] osu! is being debugged. Console attached to the process "
    "has been detected.",
    LastFMFlags.EXTRA_THREADS: "[LIKELY] A foreign thread has been detected attached to osu! This is a method "
    "usually used by cheats to run.",
    LastFMFlags.HQOSU_ASSEMBLY: "[CERTAIN] The HQOsu assembly has been detected.",
    LastFMFlags.HQOSU_FILE: "[MIXED] The presence of HQOsu files has been detected.",
    LastFMFlags.HQ_RELIFE: "[MIXED] HQOsu Relife traces found in registry. This means that the user has used the "
    "multiaccounting tool in the past, but may not be using it now.",
    LastFMFlags.AQN_SQL2LIB: "[CERTAIN] Ancient AQN library SQL2Lib detected.",
    LastFMFlags.AQN_LIBEAY32: "[CERTAIN] Use of ancient AQN version detected through library libeay32.dll",
    LastFMFlags.AQN_MENU_SOUND: "[CERTAIN] Use of ancient AQN version detected through menu sound.",
}

# Same as above but with ints to lookup.
_flag_ints = {flag.value: expl for flag, expl in _flag_expl.items()}


def get_flag_explanation(flag: LastFMFlags) -> list[str]:
    """Returns a list of strings explaining the meaning of all triggered
    flags."""

    flag_int = flag.value

    # Iterate over every single bit of `flag_int` and look up the meaning.
    res = []
    cur_bit = 0b1
    while cur_bit < flag_int:
        if flag_int & cur_bit:
            text_append = _flag_ints.get(cur_bit)

            # The flag doesnt have an explanation available, add a repr.
            if not text_append:
                text_append = f"Undocumented Flag: {LastFMFlags(cur_bit)!r}"

            res.append(text_append)

        cur_bit <<= 1

    return res


async def log_lastfm_flag(user_id: int, flag: int, flag_text: str) -> None:
    await app.state.services.database.execute(
        "INSERT INTO lastfm_flags (user_id, timestamp, flag_enum, flag_text) VALUES "
        "(:id, :timestamp, :flag, :flag_str)",
        {
            "id": user_id,
            "timestamp": int(time.time()),
            "flag": flag,
            "flag_str": flag_text,
        },
    )


async def lastfm(
    user: User = Depends(authenticate_user(Query, "us", "ha")),
    map_id_or_anticheat_flag: str = Query(..., alias="b"),
) -> Response:
    if not map_id_or_anticheat_flag.startswith("a"):
        return Response(b"-3")

    flags = LastFMFlags(int(map_id_or_anticheat_flag.removeprefix("a")))
    expl_str = "\n".join(get_flag_explanation(flags))

    await log_lastfm_flag(user.id, flags.value, expl_str)

    logging.info(f"{user} has been flagged with {flags!r}!\n{expl_str}")
    return Response(b"-3")
