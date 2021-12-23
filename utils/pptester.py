# A tester to simulate and estimate the changes to a user caused by a pp
# calculation change. I wrote this while incredibly bored so the code quality
# is not the best.
from cli_utils import get_loop, perform_startup_requirements
from tabulate import tabulate
from constants.c_modes import CustomModes
from constants.modes import Mode
from globals.connections import sql
from globals.caches import name
from dataclasses import dataclass
from objects.beatmap import Beatmap
from objects.score import Score
from colorama import Fore
from progressbar import progressbar
from logger import error, info
import sys

def calc_weighed_pp(scores: tuple[float]) -> tuple[float, float]:
    """Calculates the weighted pp for a user's scores."""
    t_pp = 0.0

    for idx, s_pp in enumerate(scores):
        t_pp += s_pp * (0.95 ** idx)

    return t_pp

async def fetch_user_scores(user_id: int, c_mode: CustomModes,
                            mode: Mode) -> tuple[float, tuple[int, float]]:
    """Fetches the score id and pp for a user's top 100 scores alongside
    calculating the estimated total PP for the user."""
    scores_db = await sql.fetchall(
        ("SELECT s.id, s.pp FROM {t} s RIGHT JOIN beatmaps b ON "
        "s.beatmap_md5 = b.beatmap_md5 WHERE s.completed = 3 AND "
        "s.play_mode = {m_val} AND b.ranked IN (3,2) AND s.userid = %s "
        "ORDER BY s.pp DESC LIMIT 100")
        .format(t = c_mode.db_table, m_val = mode.value),
        (user_id,)
    )

    t_pp = calc_weighed_pp([s[1] for s in scores_db])

    return t_pp, scores_db

@dataclass
class PPChangeResult:
    """A result for the recalculation of a single score."""

    score: Score
    old_pp: float
    new_pp: float

    @classmethod
    async def from_score(cls, score: Score) -> "PPChangeResult":
        """Creates a new PPChangeResult object from a score object."""

        old_pp = score.pp
        new_pp = await score.calc_pp()

        return cls(
            score, old_pp, new_pp
        )
    
    @property
    def difference_formatted(self) -> str:
        """Formats the difference using colours."""

        pp_diff = round(self.new_pp - self.old_pp, 2)
        pp_show = round(self.new_pp, 2)
        colour = Fore.GREEN if pp_diff > 0 else Fore.RED if pp_diff < 0 else Fore.YELLOW
        sign = "+" if pp_diff > 0 else ""

        return f"{pp_show}pp {colour}({sign}{pp_diff}){Fore.RESET}"
    
    def as_tuple(self) -> tuple[str, str, float, float]:
        """Returns the object as a tuple for printing."""

        return (
            self.score.id,
            f"{self.score.username} ({self.score.user_id})",
            self.score.bmap.song_name,
            self.difference_formatted,
        )

TABLE_HEADERS = (
    "Score", "User", "Song Name", "PP"
)
DIVIDER = "-" * 15

@dataclass
class PPChangeCalc:
    """A simple tool for testing the effects of a pp calc change on a user."""

    user_id: int
    username: str
    mode: Mode
    c_mode: CustomModes
    old_pp_values: list[tuple[int, float]]
    new_total_pp_values: list[int]
    score_diff: list[PPChangeResult]
    new_total_pp: float = 0.0
    old_total_pp: float = 0.0

    async def load_old_data(self) -> None:
        """Loads the data for the user and saves it in the object."""

        info("Loading current user info...")
        self.old_total_pp, self.old_pp_values = await fetch_user_scores(
            self.user_id, self.c_mode, self.mode
        )
    
    @property
    def display_difference(self) -> str:
        """Displays the total pp difference for user."""

        difference = round(self.new_total_pp - self.old_total_pp)
        sign = "+" if difference > 0 else ""
        colour = Fore.GREEN if difference > 0 else Fore.RED if difference < 0 else Fore.YELLOW

        return (f"{self.username}'s (estimated) total PP change: {self.old_total_pp:.2f} -> {self.new_total_pp:.2f} "
                f"{colour}({sign}{difference}pp){Fore.RESET}")
        
    async def load_score_diff(self) -> None:
        """Loads the score diff results."""

        info("Loading scores and calculating PP for user....")
        for score_id, _ in progressbar(self.old_pp_values):
            score = await Score.from_db(score_id, self.c_mode)
            self.score_diff.append(await PPChangeResult.from_score(score))
        
        self.new_total_pp = round(calc_weighed_pp([s.score.pp for s in self.score_diff]), 2)
    
    def display(self) -> None:
        """Displays the scores in a console table."""

        print(tabulate([a.as_tuple() for a in self.score_diff], headers= TABLE_HEADERS))
    
    @classmethod
    async def perform_full(cls, user_id: int, mode: Mode, c_mode: CustomModes):
        """Performs a full recalculation simulation for a user."""

        self = cls(
            user_id= user_id,
            username= await name.name_from_id(user_id),
            mode= mode,
            c_mode= c_mode,
            # Defaults
            old_pp_values= [],
            new_total_pp_values= [],
            score_diff= [],
        )

        await self.load_old_data()
        await self.load_score_diff()

        self.display()
        print(DIVIDER)
        print(self.display_difference)

def invalid_args_err(info: str) -> None:
    """Displays an error and closes the program."""

    error("Supplied incorrect arguments!\n" + info + "\nConsult the README.md "
          "for documentation of proper usage!")
    raise SystemExit(1)

# Args: [userid] [mode] [c_mode]
def parse_args() -> dict:
    """Simple hardcoded CLI arg parser."""

    args = sys.argv[1:]
    arg_count = len(args)

    if not args: invalid_args_err("No args specified!")

    try:
        user_id = int(args[0])
        mode = Mode(int(args[1]))
        c_mode = CustomModes(int(args[2]))
    except ValueError:
        invalid_args_err("Invalid argument types supplied!")
    except IndexError:
        invalid_args_err(f"Expected 3 command arguments to be supplied (received {arg_count})")
    
    return {
        "user_id": user_id,
        "mode": mode,
        "c_mode": c_mode
    }

def main():
    """Core functionality of the CLI."""

    info("Loading PPTester...")

    # Make sure server is prepared for operation.
    loop = get_loop()
    perform_startup_requirements()

    # Parse cli data
    data_parsed = parse_args()

    # Perform our recalc and close.
    loop.run_until_complete(
        PPChangeCalc.perform_full(
            **data_parsed
        )
    )

if __name__ == "__main__": main()
