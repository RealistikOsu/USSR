# The privilege cache to avoid per-request SQL queries.
from typing import Dict, Optional
from globals.connections import sql
from constants.privileges import Privileges

class PrivilegeCache:
    """Stores the privileges of all users in memory for rapid lookups."""

    def __init__(self) -> None:
        self.privileges: Dict[int, Privileges] = {}
    
    async def full_load(self) -> None:
        """Loads ALL privileges to memory from the database.
        
        Note:
            This is an INTENSIVE OPERATION. Use rarely.
        """

        ranks_db = await sql.fetchall("SELECT id, privileges FROM users")

        self.privileges = {user_id: Privileges(priv) for user_id, priv in ranks_db}
    
    async def get_privilege(self, user_id: int) -> Optional[int]:
        """Returns the privilege bitwise for a user if found. Else returns None.
        
        Args:
            user_id (int): The database ID of the user to get the privilege of.
        """

        # Theyre already cached (should be the case 9/10 times).
        if privs := self.privileges.get(user_id): return privs

        # Try to load them. Return what we got.
        await self.load_singular(user_id)
        return self.privileges.get(user_id)
    
    async def load_singular(self, user_id: int) -> None:
        """Caches the privileges for a singular user and saves to memory.
        
        Note:
            This function does NOT raise an exception if the user is not found.
            It may also be used as an update privilege function.
        
        Args:
            user_id (int): The database ID for the user to cache.
        """

        priv_db = await sql.fetchcol("SELECT privileges FROM users WHERE id = %s",
                           (user_id,))
        if priv_db is None: return
        self.privileges[user_id] = Privileges(priv_db)
    
    def __len__(self) -> int: return len(self.privileges)
