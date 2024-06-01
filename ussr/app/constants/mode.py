from __future__ import annotations

from enum import IntEnum
from functools import cached_property

from app.constants.mods import Mods

mode_str = (
    "osu!std",
    "osu!taiko",
    "osu!catch",
    "osu!mania",
    "std!rx",
    "taiko!rx",
    "catch!rx",
    "std!ap",
)

RELAX_OFFSET = 1_073_741_823
AP_OFFSET = 2_000_000_000


class Mode(IntEnum):
    STD = 0
    TAIKO = 1
    CATCH = 2
    MANIA = 3

    STD_RX = 4
    TAIKO_RX = 5
    CATCH_RX = 6
    STD_AP = 7

    def __repr__(self) -> str:
        return mode_str[self.value]

    @cached_property
    def as_vn(self) -> int:
        if self.value in (0, 4, 7):
            return 0
        elif self.value in (1, 5):
            return 1
        elif self.value in (2, 6):
            return 2
        else:
            return self.value

    @cached_property
    def relax(self) -> bool:
        return self.value > 3 and self.value != 7

    @cached_property
    def autopilot(self) -> bool:
        return self.value == 7

    @cached_property
    def scores_table(self) -> str:
        if self.relax:
            return "scores_relax"

        if self.autopilot:
            return "scores_ap"

        return "scores"

    @cached_property
    def stats_table(self) -> str:
        if self.relax:
            return "rx_stats"

        if self.autopilot:
            return "ap_stats"

        return "users_stats"

    @cached_property
    def stats_prefix(self) -> str:
        mode_vn = self.as_vn

        return {
            Mode.STD: "std",
            Mode.TAIKO: "taiko",
            Mode.CATCH: "ctb",
            Mode.MANIA: "mania",
        }[mode_vn]

    @cached_property
    def redis_leaderboard(self) -> str:
        suffix = ""

        if self.relax:
            suffix = "_relax"
        elif self.autopilot:
            suffix = "_ap"

        return f"leaderboard{suffix}"

    @cached_property
    def relax_int(self) -> int:
        if self.relax:
            return 1

        if self.autopilot:
            return 2

        return 0

    @cached_property
    def relax_str(self) -> str:
        if self.relax:
            return "RX"

        if self.autopilot:
            return "AP"

        return "VN"

    @cached_property
    def sort(self) -> str:
        return "pp" if self.value > 3 else "score"

    @classmethod
    def from_offset(cls, score_id: int) -> Mode:
        # IMPORTANT NOTE: this does not return the correct MODE, just the correct vn/rx/ap representation
        if RELAX_OFFSET < score_id < AP_OFFSET:
            return Mode.STD_RX
        elif score_id > AP_OFFSET:
            return Mode.STD_AP

        return Mode.STD

    @classmethod
    def from_lb(cls, mode: int, mods: int) -> Mode:
        if mods & Mods.RELAX:
            if mode == 3:
                return Mode.MANIA

            return Mode(mode + 4)
        elif mods & Mods.AUTOPILOT:
            if mode != 0:
                return Mode.STD

            return Mode.STD_AP

        return Mode(mode)
