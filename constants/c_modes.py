from enum import IntEnum
from typing import Optional
from .mods import Mods
from .modes import Mode

class CustomModes(IntEnum):
    """An enumeration of the custom modes implemented by the private server."""

    VANILLA = 0
    RELAX = 1
    AUTOPILOT = 2

    def to_db_suffix(self) -> str:
        """Returns the database table (for redis and sql) suffix for the given
        `c_mode`."""

        return _db_suffixes[self]
    
    @staticmethod
    def all() -> tuple["CustomModes", ...]:
        """Returns a tuple of all possible instances of `CustomModes`."""

        return _all_c_modes
    
    @classmethod
    def from_mods(cls, mods: Mods, mode: Optional[Mode] = None) -> 'CustomModes':
        """Creates an instance of `CustomModes` from a mod combo."""

        # Mania only supports vanilla
        if mode is Mode.MANIA: return cls.VANILLA
        elif mods & Mods.AUTOPILOT: return cls.AUTOPILOT
        elif mods & Mods.RELAX: return cls.RELAX
        return cls.VANILLA
    
    @classmethod
    def from_score_id(cls, score_id: int) -> 'CustomModes':
        """Calculates the c_mode for a score using score offsets.
        
        Args:
            score_id (int): The score ID that the `CustomMode` will be
                calculated from.
        """

        if RELAX_OFFSET < score_id < AP_OFFSET: return cls.RELAX
        elif score_id > AP_OFFSET: return cls.AUTOPILOT
        return cls.VANILLA

    @property
    def uses_ppboard(self) -> bool:
        """Bool corresponding to whether the c_mode offers pp leaderboards
        by default."""

        return self.value in _uses_ppboard
    
    @property
    def db_table(self) -> str:
        """Returns the MySQL database table for the scores of this `c_mode`."""

        return "scores" + self.to_db_suffix()
    
    @property
    def db_prefix(self) -> str:

        return _db_prefixes[self]
    
    @property
    def acronym(self) -> str:
        """Returns the acronym for the c_mode."""

        return _acronyms[self]
    
    @property
    def name(self) -> str:
        """Returns the lowercase name of the c_mode."""

        return _word[self]
    
    @property
    def compatible_modes(self) -> tuple[Mode, ...]:
        """Returns a tuple of all Modes that are able to be used with the current
        `CustomMode` within the game."""

        return _available_modes[self]

_db_suffixes = {
    CustomModes.VANILLA: "",
    CustomModes.RELAX: "_relax",
    CustomModes.AUTOPILOT: "_ap"
}

_db_prefixes = {
    CustomModes.VANILLA: "users",
    CustomModes.RELAX: "rx",
    CustomModes.AUTOPILOT: "ap"
}

_acronyms = {
    CustomModes.VANILLA: "VN",
    CustomModes.RELAX: "RX",
    CustomModes.AUTOPILOT: "AP",
}

_word = {
    CustomModes.VANILLA: "vanilla",
    CustomModes.RELAX: "relax",
    CustomModes.AUTOPILOT: "autopilot",
}

_uses_ppboard = (
    CustomModes.RELAX,
    CustomModes.AUTOPILOT,
)

_all_c_modes = (
    CustomModes.VANILLA,
    CustomModes.RELAX,
    CustomModes.AUTOPILOT,
)

_available_modes = {
    CustomModes.VANILLA: (Mode.STANDARD, Mode.TAIKO, Mode.CATCH, Mode.MANIA),
    CustomModes.RELAX: (Mode.STANDARD, Mode.TAIKO, Mode.CATCH),
    CustomModes.AUTOPILOT: (Mode.STANDARD,),
}

# Score offsets for each mode, avoiding queries.
RELAX_OFFSET = 1_073_741_823
AP_OFFSET = 2_000_000_000
