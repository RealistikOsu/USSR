from enum import IntEnum
from colorama import Fore

class Status(IntEnum):
    """An enum of beatmap statuses."""
    
    GRAVEYARD = -2
    NOT_SUBMITTED = -1
    PENDING = 0
    UPDATE_AVAILABLE = 1
    RANKED = 2
    APPROVED = 3
    QUALIFIED = 4
    LOVED = 5

    @classmethod
    def from_direct(self, value: int) -> 'Status':
        """Convert current direct status to osu! normal."""
        return _normal_direct_conv.get(value, self.PENDING)
    
    @classmethod
    def from_api(self, value: int) -> 'Status':
        """Converts an osu!api status to a regular one."""

        # This is neat thanks james
        if value <= 0: return self.PENDING
        else: return self(value + 1)

    def to_direct(self) -> int:
        """Converts osu statuses to osu!direct ones."""
        return _direct_normal_conv.get(self.value, self.value)

_direct_normal_conv = {
    Status.PENDING: 0,
    Status.QUALIFIED: 3,
    Status.RANKED: 1,
    Status.LOVED: 4,
    Status.GRAVEYARD: -2,
    Status.APPROVED: 1
}

_normal_direct_conv = {
    0: Status.RANKED,
    2: Status.PENDING,
    3: Status.QUALIFIED,
    5: Status.GRAVEYARD,
    7: Status.RANKED,
    8: Status.LOVED
}

class LeaderboardTypes(IntEnum):
    """osu! in-game leaderboards types. Taken from osu! `RankingType` enum at
    `SongSelection.cs` line 3180."""

    LOCAL: int   = 0 # Not used online.
    GLOBAL: int  = 1 # Regular top leaderboards.
    MOD: int     = 2 # Leaderboards for a specific mod combo.
    FRIENDS: int = 3 # Leaderboard containing only the user's friends.
    COUNTRY: int = 4 # Leaderboards containing only people from the user's nation.

FETCH_TEXT = ("No Result", "Cache", "MySQL", "API", "Local")

FETCH_COL = (
    Fore.RED,     # None
    Fore.GREEN,   # Cache
    Fore.BLUE,    # MySQL
    Fore.YELLOW,  # API
    Fore.MAGENTA, # Local
)
class FetchStatus(IntEnum):
    """Statuses representing how information was fetched. Mostly meant for
    logging purposes."""
    NONE = 0 # No information was fetched.
    CACHE = 1 # Information was fetched from cache.
    MYSQL = 2 # Information was fetched from MySQL.
    API = 3 # Information was fetched from the API.
    LOCAL = 4 # Information deduced from other information.

    @property
    def result_exists(self) -> bool:
        """Whether the fetch result value means there is a valid result present."""

        return self.value > 0

    @property
    def colour(self) -> str:
        """Returns the colorama colour that should be used for the status."""

        return FETCH_COL[self.value]

    @property
    def console_text(self) -> str:
        """Returns the text string to be used in loggign."""

        return f"{self.colour}{FETCH_TEXT[self.value]}{Fore.WHITE}"
