from logger import error, info
from lenhttp import Application, Endpoint
from config import conf
import traceback

# Uvloop is a significantly faster loop.
try:
    import uvloop
    uvloop.install()
except ImportError: pass

# Globals innit.
from globs.conn import connect_sql, connect_redis
from globs.caches import initialise_cache

# Load handlers.
from handlers.direct import direct_get_handler, download_map, get_set_handler
from handlers.leaderboards import leaderboard_get_handler

# Must return True for success or else server wont start.
STARTUP_TASKS = (
    connect_sql,
    connect_redis,
    initialise_cache,
)

async def perform_startup():
    """Runs all of the startup tasks, checking if they all succeed. If not,
    `SystemExit` will be raised."""

    info("Running startup tasks...")
    try:
        if not all([await c() for c in STARTUP_TASKS]):
            error("Not all startup tasks succeeded! Check logs above.")
            raise SystemExit(1)
    except Exception:
        error("Error running startup task!" + traceback.format_exc())
        raise SystemExit(1)
    info("Doned.")

app = Application(
    port= conf.http_port,
    logging= conf.framework_log,
    routes= [
        Endpoint("/web/osu-osz2-getscores.php", leaderboard_get_handler),
        Endpoint("/web/osu-search.php", direct_get_handler),
        Endpoint("/web/osu-search-set.php", get_set_handler),
        Endpoint("/d/<map_id>", download_map)
    ]
)

app.add_task(perform_startup)

app.start()
