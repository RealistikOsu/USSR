# Globals init.
from globs.conn import connect_sql
from logger import error, info

# Must return True for success or else server wont start.
STARTUP_TASKS = (
    connect_sql,
)

async def perform_startup():
    """Runs all of the startup tasks, checking if they all succeed. If not,
    `SystemExit` will be raised."""

    info("Running startup tasks...")

    if not all(await c() for c in STARTUP_TASKS):
        error("Not all startup tasks succeeded! Check logs above.")
        raise SystemExit(1)
