# The clan cache to avoid weird joins.
from typing import Dict, Optional
from globals.connections import sql

# The clan cache is taken from https://github.com/RealistikOsu/lets/blob/master/helpers/clan_helper.py
# I wrote it myself for the RealistikOsu lets and this is just an async port.
class ClanCache:
    """Tackles probably the 2nd most inefficient part of lets, the clan
    system. Prior to this, for each score, LETS would run an SQL query to grab
    each user's clan per score per lb and I thought that was meme worthy.
    Rosu encounters CPU usage spikes to this has to be done I am afraid.
    
    Cool system tho, accurately keeps track of clans while maintaining
    exact same functionality and better performance.
    
    **This only caches clan tags per user.**
    """

    def __init__(self) -> None:
        """Sets defaults for the cache."""

        # Indexed user_id: clan_tag
        self._cached_tags: Dict[int, str] = {}
    
    async def full_load(self) -> None:
        """Caches all clan members within the database.
        
        Note:
            This fully wipes the current cache and refreshes it.
        """

        self._cached_tags.clear()

        # Grab all clan memberships from db.
        clans_db = await sql.fetchall(
            "SELECT uc.user, c.tag FROM user_clans uc "
            "INNER JOIN clans c ON uc.clan = c.id"
        )

        # Save all to cache.
        for u, tag in clans_db:
            self._cached_tags[u] = tag
    
    async def cache_individual(self, user_id: int) -> None:
        """Caches an individual's clan (singular person) to cache. Meant for
        handling clan updates.
        
        Args:
            user_id (int): The user for who to update the cached tag for.
        """

        # Delete them if they already had a value cached.
        try: del self._cached_tags[user_id]
        except KeyError: pass

        # Grab their tag.
        clan_db = await sql.fetchcol(
            "SELECT c.tag FROM clans c INNER JOIN "
            "user_clans uc ON c.id = uc.clan WHERE uc.user = %s LIMIT 1",
            (user_id,)
        )

        if not clan_db: return # Nothing... Keep it empty and get will just return noen.

        # cache their tag.
        self._cached_tags[user_id] = clan_db
    
    def get(self, user_id: int) -> Optional[str]:
        """Returns the clan tag for the given user.
        
        Args:
            user_id (int): The user you want to grab the clan tag for.
        """

        return self._cached_tags.get(user_id)
    
    @property
    def cached_count(self) -> int:
        """Number of tags cached."""

        return len(self._cached_tags)
    
    def __len__(self) -> int: return self.cached_count
