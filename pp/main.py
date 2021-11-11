from consts.c_modes import CustomModes
from consts.modes import Mode
from .peace import CalculatorPeace
from typing import TYPE_CHECKING, Type
if TYPE_CHECKING:
    from objects.score import Score

# Base class for type hints.
class BaseCalculator:
    """A base type-hinting class."""

    mode: int 
    mods: int 
    n50: int  
    n100: int 
    n300: int 
    katu: int 
    combo: int
    score: int
    acc: float
    bmap_id: int

    def __init__(self): ...
    @classmethod
    def from_score(cls, score: 'Score') -> 'BaseCalculator': ...
    async def calculate(self) -> tuple[float, float]: ...

def select_calculator(mode: Mode, c_mode: CustomModes) -> Type[BaseCalculator]:
    """Selects the PP calculator to use based on multiple factors."""

    # TODO: Add more calculator selection logic.
    return CalculatorPeace
