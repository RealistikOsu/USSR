from enum import IntEnum

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
    TOP: int     = 1 # Regular top leaderboards.
    MOD: int     = 2 # Leaderboards for a specific mod combo.
    FRIENDS: int = 3 # Leaderboard containing only the user's friends.
    COUNTRY: int = 4 # Leaderboards containing only people from the user's nation.
