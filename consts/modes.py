from enum import IntEnum

class Mode(IntEnum):
    STANDARD = 0
    TAIKO = 1
    CATCH = 2
    MANIA = 3

    def to_db_str(self) -> str:
        """Converts a mod enum to a `str` used in the database."""

        return _mode_str_conv[self.value]

_mode_str_conv = {
    Mode.STANDARD: "std",
    Mode.TAIKO: "taiko",
    Mode.CATCH: "ctb",
    Mode.MANIA: "mania"
}
