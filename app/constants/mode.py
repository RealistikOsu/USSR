from __future__ import annotations

from enum import IntEnum
from functools import cached_property
from typing import Literal

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

RELAX_OFFSET = 500000000
AP_OFFSET = 6148914691236517204


class Mode(IntEnum):
    STD = 0
    TAIKO = 1
    CATCH = 2
    MANIA = 3

    STD_RX = 4
    TAIKO_RX = 5
    CATCH_RX = 6

    STD_AP = 8

    def __repr__(self) -> str:
        return mode_str[self.value]

    @cached_property
    def as_vn(self) -> int:
        return self.value % 4

    @cached_property
    def relax(self) -> bool:
        return self.value in (self.STD_RX, self.TAIKO_RX, self.CATCH_RX)

    @cached_property
    def autopilot(self) -> bool:
        return self is self.STD_AP

    @cached_property
    def scores_table(self) -> Literal["scores_relax", "scores_ap", "scores"]:
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
        }[Mode(mode_vn)]

    @cached_property
    def redis_leaderboard(self) -> str:
        if self.relax:
            return "relaxboard"
        elif self.autopilot:
            return "autoboard"

        return "leaderboard"

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
    def sort(self) -> Literal["pp", "score"]:
        return "pp" if self.value > 3 else "score"

    @classmethod
    def from_offset(cls, score_id: int) -> Mode:
        # IMPORTANT NOTE: this does not return the correct MODE, just the correct vn/rx/ap representation
        if score_id < RELAX_OFFSET:
            return Mode.STD_RX
        elif score_id >= AP_OFFSET:
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
