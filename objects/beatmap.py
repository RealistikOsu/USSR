from dataclasses import dataclass
from consts.modes import Mode
from consts.statuses import Status

@dataclass
class Beatmap:
    """An object representing an osu! beatmap."""

    id: int = 0
    set_id: int = 0
    md5: str = ""
    # I personally would store separately but ripple db
    song_name: str = ""
    ar: float = 0.0
    od: float = 0.0
    mode: Mode = Mode(0)
    max_combo: int = 0
    hit_length: int = 0
    bpm: int = 0
    rating: int = 10
    playcount: int = 0
    passcount: int = 0
    last_update: int = 0
    status: Status = Status(0)
    # Ripple schema difficulties
    difficulty_std: float = 0.0
    difficulty_taiko: float = 0.0
    difficulty_ctb: float = 0.0
    difficulty_mania: float = 0.0

    @property
    def difficulty(self) -> float:
        """Returns the star difficulty for the beatmap's main mode."""

        return {
            modes.STANDARD: self.difficulty_std,
            modes.TAIKO: self.difficulty_taiko,
            modes.CATCH: self.difficulty_ctb,
            modes.MANIA: self.difficulty_mania
        }[self.mode]
