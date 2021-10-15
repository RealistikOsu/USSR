# Simple wrapper around the peace PP calc
from peace_performance_python.objects import Calculator, Beatmap
from typing import TYPE_CHECKING
from helpers.beatmap import fetch_osu_file

if TYPE_CHECKING:
    from objects.score import Score

class CalculatorPeace:
    """A thin wrapper around the peace PP calulcator."""

    __slots__ = ("score", "bmap")

    def __init__(self, score: 'Score') -> None:
        self.score = score
        self.bmap = score.bmap
    
    async def calculate(self) -> float:
        """Calculates the PP for the given score.
        
        Note:
            May download the map from the interwebs, meaning it can be slo.
        
        Returns:
            The PP for the score.
        """

        b = Beatmap(await fetch_osu_file(self.bmap.id))
        c = Calculator(
            mode= self.score.mode.value,
            mods= self.score.mods.value,
            n50= self.score.count_50,
            n100= self.score.count_100,
            n300= self.score.count_300,
            katu= self.score.count_katu,
            combo= self.score.max_combo,
            score= self.score.score
        )

        res = c.calculate(b)
        return res.pp, res.stars
