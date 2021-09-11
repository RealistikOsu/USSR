from logger import error, info

# Globals init.
from globs.conn import connect_sql
from globs.caches import initialise_cache

# Must return True for success or else server wont start.
STARTUP_TASKS = (
    connect_sql,
    initialise_cache,
)

async def perform_startup():
    """Runs all of the startup tasks, checking if they all succeed. If not,
    `SystemExit` will be raised."""

    info("Running startup tasks...")

    if not all(await c() for c in STARTUP_TASKS):
        error("Not all startup tasks succeeded! Check logs above.")
        raise SystemExit(1)
