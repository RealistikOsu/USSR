# Ruri mode but it helps us do less joins (can be expensive in big cases) and
# assists with name -> ID lookups and vice-versa
from typing import Dict, Optional
from globals.connections import sql

BASE_QUERY = "SELECT id, username, username_safe FROM users "

class UsernameCache:
    """Stores ID->Username etc combinations in memory for quick access."""
    def __init__(self) -> None:
        self.id_name_cache: Dict[int, str] = {}
        # Reverse above except safe names.
        self.safe_id_cache: Dict[str, int] = {}
    
    async def full_load(self) -> None:
        """Loads all username - id combos to memory for access."""

        names_db = await sql.fetchall(BASE_QUERY)
        self.id_name_cache = {user_id: name for user_id, name, _ in names_db}
        self.safe_id_cache = {safe_name: user_id for user_id, _, safe_name in names_db}
    
    async def name_from_id(self, user_id: int) -> Optional[str]:
        """Fetches a user's username from their user_id.
        
        Args:
            user_id (int): The database ID of the user to request the name
                for.
        """

        name = self.id_name_cache.get(user_id)
        # Try loading it from db (maybe new user)
        if not name:
            await self.load_from_id(user_id)
            name = self.id_name_cache.get(user_id)

        return name
    
    async def id_from_safe(self, s_name: str) -> Optional[int]:
        """Fetches a user's `user_id` using their safe variant of their name.
        
        Args:
            s_name (str): The safe variant of a name (see `helpers.user.safe_name`
                for more details).
        """

        user_id = self.safe_id_cache.get(s_name)
        if not user_id:
            await self.load_from_safe(s_name)
            user_id = self.safe_id_cache.get(s_name)

        return user_id
    
    # TODO: Probably on register would be cool.
    async def load_from_id(self, user_id: int) -> None:
        """Caches a singular user from their id to the cache.
        I am really tired writing this but you get the point.
        """

        user_db = await sql.fetchone(
            BASE_QUERY + "WHERE id = %s", (user_id,)
        )
        if not user_db: return

        user_id, name, safe_name = user_db

        self.safe_id_cache[safe_name] = user_id
        self.id_name_cache[user_id] = name
    
    async def load_from_safe(self, safe_name: str) -> None:
        """Someone please write this."""

        user_db = await sql.fetchone(
            BASE_QUERY + "WHERE username_safe = %s LIMIT 1", (safe_name,) 
        )
        if not user_db: return

        user_id, name, safe_name = user_db

        self.safe_id_cache[safe_name] = user_id
        self.id_name_cache[user_id] = name
    
    def __len__(self) -> int: return len(self.id_name_cache)
