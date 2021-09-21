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
        return {
            0: self.RANKED,
            2: self.PENDING,
            3: self.QUALIFIED,
            4: None,
            5: self.GRAVEYARD,
            7: self.RANKED,
            8: self.LOVED
        }.get(value, self.PENDING)

    def to_direct(self) -> int:
        """Converts osu statuses to osu!direct ones."""
        return {
            self.PENDING: 0,
            self.QUALIFIED: 3,
            self.RANKED: 1,
            self.LOVED: 4,
            self.GRAVEYARD: -2,
            self.APPROVED: 1
        }.get(self.value, self.value)
    
