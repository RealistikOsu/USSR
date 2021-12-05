# Replay related handlers.
from helpers.replays import read_replay, build_full_replay
from helpers.user import incr_replays_watched
from objects.score import Score
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

    rp = await read_replay(score_id, c_mode)
    if not rp:
        error(f"Requested non-existent replay file {score_id}.osr")
        return ERR_NOT_FOUND

    # Increment their stats.
    await incr_replays_watched(user_id, mode)

    info(f"Successfully served replay {score_id}.osr")
    return rp

async def get_full_replay_handler(req: Request, score_id) -> bytearray:
    """Retuns a fully built replay with headers. Used for web."""

    score_id = int(score_id)
    c_mode = CustomModes.from_score_id(score_id)
    score = await Score.from_db(score_id, c_mode)
    if not score: return await req.send(404, b"Score not foun!")

    rp = build_full_replay(score)
    if not rp: return await req.send(404, b"Replay not found!")

    filename = f"{score.username} - {score.bmap.song_name} ({score.id}).osr"

    info(f"Served compiled replay {score_id}!")

    req.add_header("Content-Disposition", f"attachment; filename={filename}")
    req.add_header("Content-Type", "application/octet-stream")

    return await req.send(200, rp.buffer)
