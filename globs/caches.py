from consts.c_modes import CustomModes
from consts.modes import Mode
from caches.clan import ClanCache
from caches.bcrypt import BCryptCache
from caches.priv import PrivilegeCache
from caches.username import UsernameCache
from caches.lru_cache import Cache
from logger import debug, info
from . import conn
from objects.achievement import Achievement
from helpers.user import safe_name

# Specialised Caches
name = UsernameCache()
priv = PrivilegeCache()
clan = ClanCache()
password = BCryptCache()
achievements = []

# General Caches.
beatmaps = Cache(cache_length= 120, cache_limit= 1000)

# Leaderboard caches.
vn_std   = Cache(cache_length= 120, cache_limit= 1000)
vn_taiko = Cache(cache_length= 120, cache_limit= 1000)
vn_catch = Cache(cache_length= 120, cache_limit= 1000)
vn_mania = Cache(cache_length= 120, cache_limit= 1000)

rx_std   = Cache(cache_length= 120, cache_limit= 1000)
rx_taiko = Cache(cache_length= 120, cache_limit= 1000)
rx_catch = Cache(cache_length= 120, cache_limit= 1000)

ap_std   = Cache(cache_length= 120, cache_limit= 1000)

# Leaderboard caches (personal best edition).
vn_std_pb   = Cache(cache_length= 120, cache_limit= 1000)
vn_taiko_pb = Cache(cache_length= 120, cache_limit= 1000)
vn_catch_pb = Cache(cache_length= 120, cache_limit= 1000)
vn_mania_pb = Cache(cache_length= 120, cache_limit= 1000)

rx_std_pb   = Cache(cache_length= 120, cache_limit= 1000)
rx_taiko_pb = Cache(cache_length= 120, cache_limit= 1000)
rx_catch_pb = Cache(cache_length= 120, cache_limit= 1000)

ap_std_pb   = Cache(cache_length= 120, cache_limit= 1000)

def get_lb_cache(mode: Mode, c_mode: CustomModes) -> Cache:
    """Returns a cache for the given `mode`, `c_mode` combo."""

    if c_mode.value == CustomModes.AUTOPILOT: return ap_std
    elif c_mode.value == CustomModes.RELAX: return _rx_lb_dict[mode.value]
    else: return _vn_lb_dict[mode.value]

def get_pb_cache(mode: Mode, c_mode: CustomModes) -> Cache:
    """Returns a cache for the given `mode`, `c_mode` combo."""

    if c_mode.value == CustomModes.AUTOPILOT: return ap_std_pb
    elif c_mode.value == CustomModes.RELAX: return _rx_lb_dict_pb[mode.value]
    else: return _vn_lb_dict_pb[mode.value]

_rx_lb_dict = {
    Mode.STANDARD: rx_std,
    Mode.TAIKO: rx_taiko,
    Mode.CATCH: rx_catch
}

_vn_lb_dict = {
    Mode.STANDARD: vn_std,
    Mode.TAIKO: vn_taiko,
    Mode.CATCH: vn_catch,
    Mode.MANIA: vn_mania
}

_rx_lb_dict_pb = {
    Mode.STANDARD: rx_std_pb,
    Mode.TAIKO: rx_taiko_pb,
    Mode.CATCH: rx_catch_pb
}

_vn_lb_dict_pb = {
    Mode.STANDARD: vn_std_pb,
    Mode.TAIKO: vn_taiko_pb,
    Mode.CATCH: vn_catch_pb,
    Mode.MANIA: vn_mania_pb
}

#CACHE_INITS = (
#    name.full_load,
#    priv.full_load,
#    clan.full_load
#)
async def initialise_cache() -> bool:
    """Initialises all caches, efficiently bulk pre-loading them."""

    # Doing this way for cool logging.
    await name.full_load()
    info(f"Successfully cached {len(name)} usernames!")

    await priv.full_load()
    info(f"Successfully cached {len(priv)} privileges!")

    await clan.full_load()
    info(f"Successfully cached {len(clan)} clans!")

    return True

async def achievements_load() -> bool:
    """Initialises all achievements into the cache."""

    # For fella who wants to use our new achievements system. You need database with content to fetch
    # you can use cmyuis gulag one as our system was based on it. 
    achs = await conn.sql.fetchall("SELECT * FROM ussr_achievements")
    for ach in achs:
        condition = eval(f"lambda score, mode_vn, stats: {ach[4]}")
        achievements.append(Achievement(
            id= ach[0],
            file= ach[1],
            name= ach[2],
            desc= ach[3],
            cond= condition
        ))
        
    debug(f"Loaded {len(achievements)} achievements into cache!") 
    return True

# Before this, auth required a LOT of boilerplate code.
async def check_auth(n: str, pw_md5: str) -> bool:
    """Handles authentication for a name + pass md5 auth."""

    s_name = safe_name(n)

    # Get user_id from cache.
    user_id = await name.id_from_safe(s_name)
    return await password.check_password(user_id, pw_md5)

def clear_lbs(md5: str, mode: Mode, c_mode: CustomModes) -> None:
    """Clears the leaderboards for a given map, mode and c_mode combo.
    
    Note:
        This does NOT refresh them.
        Does NOT raise an exception if lb is not already cached.

    Args:
        md5 (md5): The MD5 hash for the beatmap to clear the lb for.
        mode (Mode): The in-game mode of the leaderboard to clear.
        c_mode (CustomModes): The custom mode of the leaderboard to
            clear.
    """

    debug("Clearing the cached leaderboards for " + md5)

    c = get_lb_cache(mode, c_mode)
    c.remove_cache(md5)

# FIXME: This is INNEFFICIENT AS HELL. We could be doing over 500 iterations
# per score submitted.
def clear_pbs(md5: str, mode: Mode, c_mode: CustomModes) -> None:
    """Clears all personal bests cached for a given beatmap.
    
    Args:
        md5 (md5): The MD5 hash for the beatmap to clear the lb for.
        mode (Mode): The in-game mode of the leaderboard to clear.
        c_mode (CustomModes): The custom mode of the leaderboard to
            clear.
    """

    c = get_pb_cache(mode, c_mode)

    for t in c.get_all_keys():
        if t[1] == md5:
            debug("Removed PB from cache.")
            c.remove_cache(t)
            break
