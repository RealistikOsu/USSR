from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.constants.mode import Mode
from app.constants.mods import Mods
from app.constants.score_status import ScoreStatus


@dataclass
class Score:
    id: int
    map_md5: str

    user_id: int

    mode: Mode
    mods: Mods

    pp: float
    sr: float

    score: int
    max_combo: int
    acc: float

    n300: int
    n100: int
    n50: int
    nmiss: int
    ngeki: int
    nkatu: int

    passed: bool
    perfect: bool
    status: ScoreStatus

    time: int
    time_elapsed: int

    rank: int = 0
    old_best: Optional[Score] = None

    def osu_string(self, username: str, rank: int) -> str:
        if self.mode > Mode.MANIA:
            score = int(self.pp)
        else:
            score = self.score

        return (
            f"{self.id}|{username}|{score}|{self.max_combo}|{self.n50}|{self.n100}|{self.n300}|{self.nmiss}|"
            f"{self.nkatu}|{self.ngeki}|{int(self.perfect)}|{int(self.mods)}|{self.user_id}|{rank}|{self.time}|"
            "1"  # has replay
        )

    @property
    def db_dict(self) -> dict:
        return {
            "id": self.id,
            "beatmap_md5": self.map_md5,
            "userid": self.user_id,
            "score": self.score,
            "max_combo": self.max_combo,
            "full_combo": self.perfect,
            "mods": self.mods.value,
            "300_count": self.n300,
            "100_count": self.n100,
            "50_count": self.n50,
            "katus_count": self.nkatu,
            "gekis_count": self.ngeki,
            "misses_count": self.nmiss,
            "time": self.time,
            "play_mode": self.mode.as_vn,
            "completed": self.status.value,
            "accuracy": self.acc,
            "pp": self.pp,
            "playtime": self.time_elapsed,
        }

    @classmethod
    def from_dict(cls, result: dict) -> Score:
        return cls(
            id=result["id"],
            map_md5=result["beatmap_md5"],
            user_id=result["userid"],
            score=result["score"],
            max_combo=result["max_combo"],
            perfect=result["full_combo"],
            mods=Mods(result["mods"]),
            n300=result["300_count"],
            n100=result["100_count"],
            n50=result["50_count"],
            nkatu=result["katus_count"],
            ngeki=result["gekis_count"],
            nmiss=result["misses_count"],
            time=result["time"],
            mode=Mode.from_lb(result["play_mode"], result["mods"]),
            status=ScoreStatus(result["completed"]),
            acc=result["accuracy"],
            pp=result["pp"],
            sr=0.0,  # irrelevant in this case
            time_elapsed=result["playtime"],
            passed=result["completed"] > ScoreStatus.FAILED,
        )
