# Common functions shared between utilities.
# Hacky way to import main
import sys
from typing import Callable
sys.path.append(".")
import os
os.chdir("../")

from main import ensure_dependencies, perform_startup
import asyncio

loop = None
def get_loop() -> asyncio.AbstractEventLoop:
    """Creates an async event loop with uvloop if available."""

    # UVloop is handled by main import.
    global loop
    loop = asyncio.get_event_loop()
    return loop

def perform_startup_requirements():
    """Performs the standard startup requirements, including async ones."""
    
    if not loop: get_loop()
    ensure_dependencies()
    loop.run_until_complete(perform_startup(False))

def spl_list(l: list, chk: int) -> list[list]:
    """Splits the list `l` into `chk` chunks."""

    return [l[i::chk] for i in range(chk)]

async def perform_split_async(coro: Callable, l: list, tasks: int):
    """Splits a list into `tasks` chunks, and creates `tasks` async tasks
    of `coro` where the chunked `l` is the argument. Waits for all tasks
    to then finish."""

    lsts = spl_list(l, tasks)
    loop = asyncio.get_event_loop()
    tasks = []

    for args in lsts: tasks.append(loop.create_task(coro(args)))
    # Now wait for all tasks to finish.
    for task in tasks: await task


if __name__ == "__main__":
    raise ValueError(
        "cli_utils is not a utility, but a library shared between all of the "
        "USSR utilities."
    )
