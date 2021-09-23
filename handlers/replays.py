# Replay related handlers.
from helpers.replays import read_replay
from helpers.user import incr_replays_watched
from consts.c_modes import CustomModes
from consts.modes import Mode
from globs.conn import sql
from lenhttp import Request
from logger import info, error

BASE_QUERY = "SELECT play_mode, userid FROM {} WHERE id = %s LIMIT 1"
ERR_NOT_FOUND = b"error: no"

async def get_replay_web_handler(req: Request) -> bytes:
    """Handles the in-game replay downloads, incrementing replays watched
    appropeately.
    URL: `/web/osu-getreplay.php`
    """

    # Grab our data. TODO: Maybe auth?
    score_id = int(req.get_args["c"])
    c_mode = CustomModes.from_score_id(score_id)

    score_data_db = await sql.fetchone(
        BASE_QUERY.format(c_mode.db_table),
        (score_id,)
    )

    # Handle replay not found.
    if not score_data_db:
        error(f"Requested non-existent replay score {score_id}")
        return ERR_NOT_FOUND
    _play_mode, user_id = score_data_db
    mode = Mode(_play_mode)

    try: rp = await read_replay(score_id, c_mode)
    except FileNotFoundError:
        error(f"Requested non-existent replay file {score_id}.osr")
        return ERR_NOT_FOUND

    # Increment their stats.
    await incr_replays_watched(user_id, mode)

    info(f"Successfully served replay {score_id}.osr")
    return rp
