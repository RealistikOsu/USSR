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
    def from_direct(self, value: int):
        """Convert current direct status to osu! normal."""
        return _normal_direct_conv.get(value, self.PENDING)

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
