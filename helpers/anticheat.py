# Anticheat related helper functions.
from config import config
from constants.c_modes import CustomModes
from globals.connections import sql
from constants.anticheat import LastFMFlags
from libs.time import get_timestamp
from objects.score import Score

_caps = {
    CustomModes.VANILLA: config.PP_CAP_VN,
    CustomModes.RELAX: config.PP_CAP_RX,
    CustomModes.AUTOPILOT: config.PP_CAP_AP,
}

def get_pp_cap(mode: CustomModes) -> int:
    return _caps[mode]

async def surpassed_cap_restrict(score: Score) -> bool:
    """Checks if the user surpassed the PP cap for their mode and should
    be restricted."""

    res = score.pp > get_pp_cap(score.c_mode)
    if res:
        # TODO: Maybe cache it?
        is_verified = await sql.fetchcol(
            "SELECT 1 FROM user_badges WHERE user = %s AND "
            f"badge = {config.SRV_VERIFIED_BADGE} LIMIT 1",
            (score.user_id,)
        )
        res = not is_verified
    return res

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
    
    return res

async def log_lastfm_flag(user_id: int, flag: int, flag_text: str) -> None:
    """Logs an occasion where the user has been flagged by the LastFM anticheat
    in the database.
    
    Args:
        user_id (int): The database ID of the user that has been flagged.
        flag (int): The bitwise integer represeting which cheats have been
            flagged.
        flag_text (str): A string of text explaining the flags triggered
            (usually the result of `get_flag_explanation`).
    """

    ts = get_timestamp()
    await sql.execute(
        "INSERT INTO lastfm_flags (user_id, timestamp, flag_enum, falg_text) "
        "VALUES (%s,%s,%s,%s)",
        (user_id, ts, flag, flag_text)
    )
