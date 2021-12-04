# Parses data from replay and inserts it to database
# NOTE: An emergency tool for situations where score
# will not get submitted.
import sys
from cli_utils import perform_startup_requirements, get_loop
from globs import caches
import traceback
from libs.time import get_timestamp
from objects.stats import Stats
from objects.score import Score
from logger import error, info
from helpers.user import safe_name
from globs.conn import sql
from consts.c_modes import CustomModes
from consts.modes import Mode
from consts.mods import Mods
from consts.actions import Actions
from consts.complete import Completed
from consts.privileges import Privileges
from consts.statuses import Status
from objects.beatmap import Beatmap
from osupyparser import ReplayFile
from helpers.user import update_country_lb_pos, update_lb_pos, edit_user
from helpers.replays import write_replay
from libs.bin import BinaryWriter
from helpers.anticheat import surpassed_cap_restrict
from helpers.pep import stats_refresh, notify_new_score


async def insert_replay_data(replay_path: str):
    """Parses replay data and inserts it to database!"""

    try:
        replay = ReplayFile.from_file(replay_path)
    except Exception:
        error("Replay was unable to parse! " + traceback.format_exc())
        raise SystemExit(1)

    user_id = await caches.name.id_from_safe(safe_name(replay.player_name))
    if not replay.player_name or not user_id:
        error("Player of replay couldn't be found!")
        raise SystemExit(1)
    info("Replay parsed, performing a score submit..")

    mode = Mode(replay.mode)
    mods = Mods(replay.mods)
    c_mode = CustomModes.from_mods(mods, mode)
    bmap = await Beatmap.from_md5(replay.map_md5)
    stats = await Stats.from_id(user_id, mode, c_mode)
    privs = await caches.priv.get_privilege(user_id)

    if not bmap:
        error("Score insert failed due to no beatmap being attached.")
        raise SystemExit(1)

    s = Score(
        0,
        bmap,
        user_id,
        replay.score,
        replay.max_combo,
        replay.perfect,
        True,
        False,
        mods,
        c_mode,
        replay.n300,
        replay.n100,
        replay.n50,
        replay.nkatu,
        replay.ngeki,
        replay.nmiss,
        get_timestamp(),
        mode,
        None,
        0.0,
        0.0,
        0,  # TODO: Playtime
        0,
        "",
        0,
        replay.player_name,
    )
    s.calc_accuracy()

    if s.mods.conflict():
        await edit_user(
            Actions.RESTRICT, s.user_id, "Illegal mod combo (score submitter)."
        )
        error(f"Restricted user for 'Illegal mod combo (score submitter).'")
        raise SystemExit(1)

    dupe_check = await sql.fetchcol(  # Try to fetch as much similar score as we can.
        f"SELECT 1 FROM {s.c_mode.db_table} WHERE "
        "userid = %s AND beatmap_md5 = %s AND score = %s "
        "AND play_mode = %s AND mods = %s LIMIT 1",
        (s.user_id, s.bmap.md5, s.score, s.mode.value, s.mods.value),
    )

    if dupe_check:
        error("Score couldn't be inserted due to duplicate check!")
        raise SystemExit(1)

    info("Fetching previous best to compare..")
    prev_db = await sql.fetchone(
        f"SELECT id FROM {stats.c_mode.db_table} WHERE userid = %s AND "
        f"beatmap_md5 = %s AND completed = 3 AND play_mode = {s.mode.value} LIMIT 1",
        (s.user_id, s.bmap.md5),
    )

    prev_score = await Score.from_db(prev_db[0], s.c_mode) if prev_db else None

    info("Submitting score..")
    await s.submit()

    info("Incrementing bmap playcount.")
    await s.bmap.increment_playcount(s.passed)

    # Stat updates
    info("Updating stats..")
    stats.playcount += 1
    stats.total_score += s.score
    stats.total_hits += s.count_300 + s.count_100 + s.count_50

    add_score = s.score
    if prev_score and s.completed == Completed.BEST:
        add_score -= prev_score.score

    if s.passed and s.bmap.has_leaderboard:
        if s.bmap.status == Status.RANKED:
            stats.ranked_score += add_score
        if stats.max_combo < s.max_combo:
            stats.max_combo = s.max_combo
        if s.completed == Completed.BEST and s.pp:
            info("Performing PP recalculation..")
            await stats.recalc_pp_acc_full(s.pp)
    info("Saving stats..")
    await stats.save()

    # This is probably the most cursed way to do it.
    info("Building and saving replay data..")
    r = (
        BinaryWriter()
        .write_u8_le(replay.mode)
        .write_i32_le(replay.osu_version)
        .write_osu_string(replay.map_md5)
        .write_osu_string(replay.player_name)
        .write_osu_string(replay.replay_md5)
        .write_i16_le(replay.n300)
        .write_i16_le(replay.n100)
        .write_i16_le(replay.n50)
        .write_i16_le(replay.ngeki)
        .write_i16_le(replay.nkatu)
        .write_i16_le(replay.nmiss)
        .write_i32_le(replay.score)
        .write_i16_le(replay.max_combo)
        .write_u8_le(int(replay.perfect))
        .write_i32_le(replay.mods)
        .write_osu_string(replay.life_graph)
        .write_i64_le(replay.timestamp)
    )
    current_off = len(r.buffer)
    with open(replay_path, "rb") as stream:
        data = stream.read()

    lzma_off = int.from_bytes(  # Read int16
        data[current_off : current_off + 4], "little", signed=True
    )
    replay_raw_data = data[current_off + 4 : current_off + 4 + lzma_off]
    await write_replay(s.id, replay_raw_data, s.c_mode)

    # Update our position on the global lbs.
    if s.completed is Completed.BEST and privs & Privileges.USER_PUBLIC:
        info("Updating user's global and country lb positions...")
        args = (s.user_id, round(stats.pp), s.mode, s.c_mode)
        await update_lb_pos(*args)
        await update_country_lb_pos(*args)
        await stats.update_rank()

    # Trigger peppy stats update.
    await stats_refresh(s.user_id)

    # More anticheat checks.
    if s.completed == Completed.BEST and await surpassed_cap_restrict(s):
        await edit_user(
            Actions.RESTRICT, s.user_id, f"Surpassing PP cap as unverified! ({s.pp}pp)"
        )
        error(f"Restricted user for 'Surpassing PP cap as unverified! ({s.pp}pp)'")
        raise SystemExit(1)

    await notify_new_score(s.id)


def invalid_args_err(info: str) -> None:
    """Displays an error and closes the program."""

    error(
        "Supplied incorrect arguments!\n" + info + "\nConsult the README.md "
        "for documentation of proper usage!"
    )
    raise SystemExit(1)


def parse_args() -> dict:
    """Simple hardcoded CLI arg parser."""

    args = sys.argv[1:]
    arg_count = len(args)

    if not args:
        invalid_args_err("No args specified!")

    try:
        replay_path = args[0]
    except ValueError:
        invalid_args_err("Invalid argument types supplied!")
    except IndexError:
        invalid_args_err(
            f"Expected 1 command arguments to be supplied (received {arg_count})"
        )

    return {"replay_path": replay_path}


def main():
    """Core functionality of the CLI."""

    info("Loading Replay Inserter...")

    # Make sure server is prepared for operation.
    loop = get_loop()
    perform_startup_requirements()

    # Parse cli data
    data_parsed = parse_args()

    # Perform our recalc and close.
    loop.run_until_complete(insert_replay_data(**data_parsed))


if __name__ == "__main__":
    main()
