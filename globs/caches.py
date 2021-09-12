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
