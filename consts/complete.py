# Score completion statuses.
from enum import IntEnum

class Completed(IntEnum):
    """Completion statuses for database scores."""

    DUPLICATE = -1
    QUIT = 0
    FAILED = 1
    COMPLETE = 2
    BEST = 3
    MOD_BEST = 4

    @property
    def completed(self) -> bool:
        """Bool corresponding to whether the user finished playing the map."""

        return self.value in _map_complete

_map_complete = (
    Completed.COMPLETE,
    Completed.BEST,
    Completed.MOD_BEST,
)
