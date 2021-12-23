from constants.c_modes import CustomModes
from constants.modes import Mode
from caches.clan import ClanCache
from caches.bcrypt import BCryptCache
from caches.priv import PrivilegeCache
from caches.username import UsernameCache
from caches.lru_cache import Cache
from logger import debug, info
from . import connections
from objects.achievement import Achievement
#from helpers.user import safe_name
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from constants.statuses import Status

# Specialised Caches
name = UsernameCache()
priv = PrivilegeCache()
clan = ClanCache()
password = BCryptCache()
achievements = []

# General Caches.
beatmaps = Cache(cache_length= 120, cache_limit= 1000)
leaderboards = Cache(cache_length= 240, cache_limit= 100_000)

# Cache for statuses that require an api call to get. md5: status
no_check_md5s: dict[str, 'Status'] = {}

# Stats cache. Key = tuple[CustomModes, Mode, user_id]
stats_cache = Cache(cache_length= 240, cache_limit= 300)

def add_nocheck_md5(md5: str, st: 'Status') -> None:
    """Adds a md5 to the no_check_md5s cache.

    Args:
        md5 (str): The md5 to add to the cache.
    """

    no_check_md5s[md5] = st

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

    await achievements_load()
    info(f"Successfully cached {len(achievements)} achievements!")

    return True

async def achievements_load() -> bool:
    """Initialises all achievements into the cache."""

    # For fella who wants to use our new achievements system. You need database with content to fetch
    # you can use cmyuis gulag one as our system was based on it. 
    achs = await connections.sql.fetchall("SELECT * FROM ussr_achievements")
    for ach in achs:
        condition = eval(f"lambda score, mode_vn, stats: {ach[4]}")
        achievements.append(Achievement(
            id= ach[0],
            file= ach[1],
            name= ach[2],
            desc= ach[3],
            cond= condition
        ))

    return True

# Before this, auth required a LOT of boilerplate code.
async def check_auth(n: str, pw_md5: str) -> bool:
    """Handles authentication for a name + pass md5 auth."""

    s_name = n.rstrip().lower().replace(" ", "_")

    # Get user_id from cache.
    user_id = await name.id_from_safe(s_name)
    return await password.check_password(user_id, pw_md5)
