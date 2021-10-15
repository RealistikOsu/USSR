# The USSR Recalculator Utils. This one will be quite slow ngl......
# But it can reuse code and utils efficiently. You win some you lose some.
from typing import Generator
from consts.c_modes import CustomModes
from caches.username import BASE_QUERY
from globs.conn import sql
from dataclasses import dataclass
from objects.score import Score
from logger import debug, info, error
from asyncio import Lock
import traceback

TASK_COUNT = 4
BASE_QUERY = "SELECT id FROM {table} WHERE {cond}"

#@dataclass
#class LWScore:
#    """A low weight score class, sharing attribute names with the regular
#    `Score` object. For memory efficiency."""

async def recalc_pp(s: Score) -> None:
    """Recalculates PP for a score and saves it."""

    await s.calc_pp()
    await s.save_pp()

class ScorePool:
    """A pool holding large quantities of scores for recalculation."""

    def __init__(self, c_mode: CustomModes) -> None:
        """Creates an empty instance of """
        self.scores: list = []
        self.score_ids: list[int] = []
        self.lock = Lock()
        self.c_mode = c_mode
    
    async def fetch_scores(self, cond: str, args: tuple = ()) -> None:
        """Fetches a list of score IDs to the pool."""
        
        self.scores = [
            s[0] for s in await sql.fetchall(BASE_QUERY.format(table= self.c_mode.db_table, cond= cond))
        ]

        info(f"ScorePool fetched a total of {len(self.scores)} scores!")
    
    async def get_scores(self) -> Generator[Score]:
        """Generates score objects from score IDs in the object."""

        for score_id in self.score_ids:
            score = await Score.from_db(score_id, self.c_mode.db_table)
            if not score: continue
            yield score
    
    async def perform_sequential(self) -> None:
        """Performs a sequential recalculation of all scores."""

        count = 0
        failed = 0
        total = len(self.scores)
        async for score in self.get_scores():
            try:
                await recalc_pp(score)
                count += 1

                if count % 10 == 0:
                    info(f"Calculated {count}/{total} scores.")
            except Exception:
                failed += 1
                err = traceback.format_exc()
                error(f"Failed recalculating score {score.id} with err {err}.\n"
                      f"Total failed: {failed}")
