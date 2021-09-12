from enum import IntEnum

class CustomModes(IntEnum):
    """An enumeration of the custom modes implemented by the private server."""

    VANILLA = 0
    RELAX = 1
    AUTOPILOT = 2

    def to_db_suffix(self):
        """Returns the database table (for redis and sql) suffix for the given
        `c_mode`."""

        return __db_suffixes[self.value]
    
    @classmethod
    def from_mods(self, mods): ...

__db_suffixes = {
    CustomModes.VANILLA: "",
    CustomModes.RELAX: "_relax",
    CustomModes.AUTOPILOT: "_ap"
}
