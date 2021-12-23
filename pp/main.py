from constants.c_modes import CustomModes
from constants.modes import Mode
from typing import TYPE_CHECKING, Type
from logger import error, info
import os
if TYPE_CHECKING:
    from objects.score import Score

# Calculators
from .peace import CalculatorPeace
from .oppai import OppaiAP, OppaiRX

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
    miss: int

    def __init__(self): ...
    @classmethod
    def from_score(cls, score: 'Score') -> 'BaseCalculator': ...
    async def calculate(self) -> tuple[float, float]: ...

def select_calculator(mode: Mode, c_mode: CustomModes) -> Type[BaseCalculator]:
    """Selects the PP calculator to use based on multiple factors."""

    # TODO: Add more calculator selection logic.
    if c_mode is CustomModes.AUTOPILOT: return OppaiAP
    elif c_mode is CustomModes.RELAX and mode is Mode.STANDARD: return OppaiRX
    return CalculatorPeace

# All directories of the C based calculator.
OPPAI_DIRS = (
    "/pp/oppai-ap",
    "/pp/oppai-rx",
)

def verify_oppai() -> bool:
    """Verifies that all the oppai calculators have been compiled and are able to
    be used."""

    res = True
    loc_dir = os.getcwd()

    for dir in OPPAI_DIRS:
        if not os.path.exists(path := f"{loc_dir}{dir}/liboppai.so"):
            # We don't return here immediately to check all directories for
            # possible errors.
            res = False
            error(f"Required PP calculator library {path} is missing!")
    
    return res

def build_oppai() -> None:
    """Builds the oppai calculator lib."""

    old_dir = os.getcwd()

    for dir in OPPAI_DIRS:
        info(f"Building PP calculator {dir} ...")
        os.chdir(old_dir + dir)
        # Make it executable in case
        os.system(f"chmod +x libbuild")
        os.system(f"./libbuild")
    
    os.chdir(old_dir)
