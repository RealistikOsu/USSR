from logger import (
    error,
    info,
    warning,
    DEBUG,
    ensure_log_file,
    check_log_file,
    write_log_file,
)
from lenhttp import Application, Endpoint
from config import conf
from redis_pubsub.router import pubsub_executor
from pp.main import build_oppai, verify_oppai
import traceback

# Uvloop is a significantly faster loop.
try:
    import uvloop

    uvloop.install()
except ImportError:
    pass

# Globals innit.
from globs.conn import connect_sql, connect_redis
from globs.caches import initialise_cache

# Load handlers.
from handlers.direct import direct_get_handler, download_map, get_set_handler
from handlers.leaderboards import leaderboard_get_handler
from handlers.replays import get_replay_web_handler, get_full_replay_handler
from handlers.screenshot import upload_image_handler
from handlers.score_sub import score_submit_handler
from handlers.rippleapi import status_handler, pp_handler
from handlers.misc import (
    lastfm_handler,
    getfriends_handler,
    osu_error_handler,
    beatmap_rate_handler,
    get_seasonals_handler,
    bancho_connect,
)

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
    refresh_leaderboard_pubsub,
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
    (drop_bmap_cache_pubsub, "ussr:bmap_decache"),
    (refresh_leaderboard_pubsub, "ussr:lb_refresh"),
)


async def create_redis_pubsub():
    """Creates all the subscriptions for redis `publish` events."""

    for coro, name in PUBSUB_REGISTER:
        await pubsub_executor(name, coro)


async def perform_startup(redis: bool = True):
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
    if not redis:
        return
    try:
        await create_redis_pubsub()
        info(f"Created {len(PUBSUB_REGISTER)} Redis PubSub listeners!")
    except Exception:
        error("Error creating Redis PubSub listeners! " + traceback.format_exc())
        raise SystemExit(1)


def server_start():
    """Handles a regular start of the server."""

    app = Application(
        unix=conf.http_sock,
        logging=DEBUG,
        routes=[
            # osu web endpoints
            Endpoint("/web/osu-osz2-getscores.php", leaderboard_get_handler),
            Endpoint("/web/osu-search.php", direct_get_handler),
            Endpoint("/web/osu-search-set.php", get_set_handler),
            Endpoint("/d/<map_id>", download_map),
            Endpoint("/web/osu-getreplay.php", get_replay_web_handler),
            Endpoint("/web/osu-screenshot.php", upload_image_handler, ["POST"]),
            Endpoint(
                "/web/osu-submit-modular-selector.php", score_submit_handler, ["POST"]
            ),
            Endpoint("/web/lastfm.php", lastfm_handler),
            Endpoint("/web/osu-getfriends.php", getfriends_handler),
            Endpoint("/web/osu-error.php", osu_error_handler, ["POST"]),
            Endpoint("/web/osu-rate.php", beatmap_rate_handler),
            Endpoint("/web/osu-getseasonal.php", get_seasonals_handler),
            Endpoint("/web/bancho_connect.php", bancho_connect),
            # Ripple API endpoints
            Endpoint("/api/v1/status", status_handler),
            Endpoint("/api/v1/pp", pp_handler),
            # Frontend Endpoints
            Endpoint("/web/replays/<score_id>", get_full_replay_handler),
        ],
    )

    write_log_file("Server started!")

    app.add_task(perform_startup)
    app.start()


# tuples of checker and fixer functions.
DEPENDENCIES = (
    (verify_oppai, build_oppai),
    (check_log_file, ensure_log_file),
)


def ensure_dependencies():
    """Checks if all dependencies are met, and if not, attempts to fix them."""

    for checker, fixer in DEPENDENCIES:
        if not checker():
            warning(f"Dependency {checker.__name__} not met! Attempting to fix...")
            try:
                fixer()
                info("Dependency fixed!")
            except Exception:
                error("Error fixing dependency!" + traceback.format_exc())
                raise SystemExit(1)


if __name__ == "__main__":
    ensure_dependencies()
    server_start()
