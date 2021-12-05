# BCrypt password cache to accelerate password verification (~300ms acceleration)
from libs.crypt import verify_bcrypt
from typing import Dict, Optional
from globs.conn import sql

async def _fetch_bcrypt(user_id: int) -> Optional[str]:
    """Fetches the BCrypt hashed password from SQL."""

    return await sql.fetchcol(
        "SELECT password_md5 FROM users WHERE id = %s", (user_id,)
    )

class BCryptCache:
    """A cache of successful password md5s for user (may slightly weaken
    security but its like a 100x speed improvement and we deal with already
    hashed pws anyways)."""

    def __init__(self) -> None:
        self.known_correct: Dict[int, str] = {}

    def drop_cache_individual(self, user_id: int) -> None:
        """Drops the cached known correct password for a user (usually done
        on password changes).
        
        Note:
            No exception is raised if user is not cached.
        
        Args:
            user_id (int): The database ID for the user.
        """

        try: del self.known_correct[user_id]
        except KeyError: pass
    
    def cache_user_pwd(self, user_id: int, pwd: str) -> None:
        """Caches a known correct password MD5 for `user_id` for use in 
        lookups.
        
        Args:
            user_id (int): The database ID of the user you are comparing the
                password for.
            pwd (str): The MD5 hashed password.
        """

        self.known_correct[user_id] = pwd
    
    async def check_password(self, user_id: int, pwd: str) -> bool:
        """Checks if the given password matches the cached/db password for
        the user.

        Note:
            If uncached, this can take a while...
        
        Args:
            user_id (int): The database ID of the user you are comparing the
                password for.
            pwd (str): The MD5 hashed password.
        """

        # If we already have a known pwd, use that.
        if known_md5 := self.known_correct.get(user_id):
            if pwd == known_md5: return True
            # DOnt return the result directly to handle passwd changes ig.
        
        # Fetch from db and compare using bcrypt.
        user_pass = await _fetch_bcrypt(user_id)
        if not user_pass: return False # User doesnt exist. Fail.

        res = verify_bcrypt(pwd, user_pass) # Long call

        # If the result is correct, cache it.
        if res: self.cache_user_pwd(user_id, pwd)
        return res
