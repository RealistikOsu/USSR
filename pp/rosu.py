# Simple wrapper around the rosu PP calc
from __future__ import annotations

from typing import TYPE_CHECKING

from rosu_pp_py import Calculator
from rosu_pp_py import ScoreParams

from helpers.beatmap import fetch_osu_file

if TYPE_CHECKING:
    from objects.score import Score


class CalculatorROsu:
    """A thin wrapper around the rosu PP calulcator."""

    # __slots__ = ("score", "bmap")

    def __init__(self) -> None:
        """Initializes the calculator."""
        self.bmap_id = 0

        # Score Values.
        self.mode: int = None
        self.mods: int = None
        self.n50: int = None
        self.n100: int = None
        self.n300: int = None
        self.katu: int = None
        self.combo: int = None
        self.score: int = None
        self.acc: float = None
        self.miss: int = None

    @classmethod
    def from_score(cls, score: Score) -> CalculatorROsu:
        """Create a calculator from a score."""

        calc = cls()
        calc.score = score.score
        calc.bmap_id = score.bmap.id
        calc.mode = score.mode.value
        calc.mods = score.mods.value
        calc.n50 = score.count_50
        calc.n100 = score.count_100
        calc.n300 = score.count_300
        calc.katu = score.count_katu
        calc.combo = score.max_combo
        calc.acc = score.accuracy
        calc.miss = score.count_miss
        return calc

    async def calculate(self) -> tuple[float]:
        """Calculates the PP and SR for the given score.

        Note:
            May download the map from the interwebs, meaning it can be slo.

        Returns:
            The PP and SR for the score.
        """

        path = await fetch_osu_file(self.bmap_id)

        c = Calculator(str(path))
        s = ScoreParams(
            mods=self.mods,
            n50=self.n50,
            n100=self.n100,
            n300=self.n300,
            nKatu=self.katu,
            combo=self.combo,
            score=self.score,
            acc=self.acc,
            nMisses=self.miss,
        )

        (res,) = c.calculate(s)
        return res.pp, res.stars
