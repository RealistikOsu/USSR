# Simple wrapper around the peace PP calc
from peace_performance_python.objects import Calculator, Beatmap
from typing import TYPE_CHECKING
from helpers.beatmap import fetch_osu_file

if TYPE_CHECKING:
    from objects.score import Score

class CalculatorPeace:
    """A thin wrapper around the peace PP calulcator."""

    #__slots__ = ("score", "bmap")

    def __init__(self) -> None:
        """Initializes the calculator."""
        self.bmap_id = 0

        # Score Values.
        self.mode: int = 0
        self.mods: int = 0
        self.n50: int = 0
        self.n100: int = 0
        self.n300: int = 0
        self.katu: int = 0
        self.combo: int = 0
        self.score: int = 0
    
    @classmethod
    def from_score(cls, score: 'Score') -> 'CalculatorPeace':
        """Create a calculator from a score."""

        calc =  cls()
        calc.score = score.score
        calc.bmap_id = score.bmap.id
        calc.mode = score.mode.value
        calc.mods = score.mods.value
        calc.n50 = score.count_50
        calc.n100 = score.count_100
        calc.n300 = score.count_300
        calc.katu = score.count_katu
        calc.combo = score.max_combo
        return calc
    
    async def calculate(self) -> float:
        """Calculates the PP for the given score.
        
        Note:
            May download the map from the interwebs, meaning it can be slo.
        
        Returns:
            The PP for the score.
        """

        b = Beatmap(await fetch_osu_file(self.bmap_id))
        c = Calculator(
            mode= self.mode,
            mods= self.mods,
            n50= self.n50,
            n100= self.n100,
            n300= self.n300,
            katu= self.katu,
            combo= self.combo,
            score= self.score,
        )

        res = c.calculate(b)
        return res.pp, res.stars
