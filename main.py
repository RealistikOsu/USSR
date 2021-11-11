from logger import error, info, warning
from lenhttp import Application, Endpoint
from config import conf
from redis_pubsub.router import pubsub_executor
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
from handlers.replays import get_replay_web_handler
from handlers.screenshot import upload_image_handler
from handlers.score_sub import score_submit_handler
from handlers.rippleapi import status_handler, pp_handler

# Load redis pubsubs.
from redis_pubsub.ripple import (
    username_change_pubsub, 
    update_cached_privileges_pubsub,
    change_pass_pubsub,
    ban_reload_pubsub,
)
from redis_pubsub.rosu import (
    clan_update_pubsub,
)
from redis_pubsub.ussr import (
    drop_bmap_cache_pubsub,
)

# Must return True for success or else server wont start.
STARTUP_TASKS = (
    connect_sql,
    connect_redis,
    initialise_cache,
)

PUBSUB_REGISTER = (
    # Ripple ones.
    (username_change_pubsub, "peppy:change_username"),
    (update_cached_privileges_pubsub, "peppy:update_cached_stats"),
    (change_pass_pubsub, "peppy:change_pass"),
    (ban_reload_pubsub, "peppy:ban"),
    # RealistikOsu.
    (clan_update_pubsub, "rosu:clan_update"),
    # USSR
    (drop_bmap_cache_pubsub, "ussr:bmap_decache")
)

async def create_redis_pubsub():
    """Creates all the subscriptions for redis `publish` events."""

    for coro, name in PUBSUB_REGISTER: await pubsub_executor(name, coro)

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
    try:
        await create_redis_pubsub()
        info(f"Created {len(PUBSUB_REGISTER)} Redis PubSub listeners!")
    except Exception:
        error("Error creating Redis PubSub listeners! " + traceback.format_exc())
        raise SystemExit(1)

app = Application(
    port= conf.http_port,
    logging= conf.framework_log,
    routes= [
        # osu web endpoints
        Endpoint("/web/osu-osz2-getscores.php", leaderboard_get_handler),
        Endpoint("/web/osu-search.php", direct_get_handler),
        Endpoint("/web/osu-search-set.php", get_set_handler),
        Endpoint("/d/<map_id>", download_map),
        Endpoint("/web/osu-getreplay.php", get_replay_web_handler),
        Endpoint("/web/osu-screenshot.php", upload_image_handler, ["POST"]),
        Endpoint("/web/osu-submit-modular-selector.php", score_submit_handler, ["POST"]),
        # Ripple API endpoints
        Endpoint("/api/v1/status", status_handler),
        Endpoint("/api/v1/pp", pp_handler),
    ]
)

if __name__ == "__main__":
    app.add_task(perform_startup)
    app.start()
