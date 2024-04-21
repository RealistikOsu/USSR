from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from typing import Mapping
from typing import Optional

from app.constants.mode import Mode
from app.constants.mods import Mods
from app.constants.score_status import ScoreStatus
from app.models.user import User


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
    quit: bool
    full_combo: bool
    status: ScoreStatus

    time: int
    time_elapsed: int = 0  # TODO: store this in db

    online_checksum: Optional[str] = None  # optional as checksum was not always stored

    rank: int = 0

    def osu_string(self, username: str, rank: int) -> str:
        if self.mode.relax or self.mode.autopilot:
            score = int(self.pp)
        else:
            score = self.score

        return (
            f"{self.id}|{username}|{score}|{self.max_combo}|{self.n50}|{self.n100}|{self.n300}|{self.nmiss}|"
            f"{self.nkatu}|{self.ngeki}|{int(self.full_combo)}|{int(self.mods)}|{self.user_id}|{rank}|{self.time}|"
            "1"  # has replay
        )

    @property
    def db_dict(self) -> dict:
        return {
            "beatmap_md5": self.map_md5,
            "userid": self.user_id,
            "score": self.score,
            "max_combo": self.max_combo,
            "full_combo": self.full_combo,
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
            "checksum": self.online_checksum,
            # "playtime": self.time_elapsed,
        }

    @classmethod
    def from_mapping(cls, result: Mapping[str, Any]) -> Score:
        return cls(
            id=result["id"],
            map_md5=result["beatmap_md5"],
            user_id=result["userid"],
            score=result["score"],
            max_combo=result["max_combo"],
            full_combo=result["full_combo"],
            mods=Mods(result["mods"]),
            n300=result["300_count"],
            n100=result["100_count"],
            n50=result["50_count"],
            nkatu=result["katus_count"],
            ngeki=result["gekis_count"],
            nmiss=result["misses_count"],
            time=int(result["time"]),
            mode=Mode.from_lb(result["play_mode"], result["mods"]),
            status=ScoreStatus(result["completed"]),
            acc=result["accuracy"],
            pp=result["pp"],
            sr=0.0,  # irrelevant in this case
            # time_elapsed=result["playtime"],
            passed=result["completed"] > ScoreStatus.FAILED,
            quit=result["completed"] == ScoreStatus.QUIT,
            online_checksum=result["checksum"],
        )

    @classmethod
    def from_submission(cls, data: list[str], map_md5: str, user: User) -> Score:
        return Score(
            id=0,  # set later
            map_md5=map_md5,
            user_id=user.id,
            mode=Mode.from_lb(int(data[13]), int(data[11])),
            mods=Mods(int(data[11])),
            pp=0.0,  # set later
            sr=0.0,  # set later
            score=int(data[7]),
            max_combo=int(data[8]),
            acc=0.0,  # set later
            n300=int(data[1]),
            n100=int(data[2]),
            n50=int(data[3]),
            nmiss=int(data[6]),
            ngeki=int(data[4]),
            nkatu=int(data[5]),
            passed=data[12] == "True",
            quit=False,  # set later
            full_combo=data[9] == "True",
            status=ScoreStatus.FAILED,  # set later
            time=int(time.time()),
            time_elapsed=0,  # set later
            online_checksum=data[0],
        )
