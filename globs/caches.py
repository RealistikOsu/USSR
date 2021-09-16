from consts.c_modes import CustomModes
from consts.modes import Mode
from caches.clan import ClanCache
from caches.bcrypt import BCryptCache
from caches.priv import PrivilegeCache
from caches.username import UsernameCache
from caches.lru_cache import Cache
from logger import info

# Specialised Caches
name = UsernameCache()
priv = PrivilegeCache()
clan = ClanCache()
password = BCryptCache()

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
