# USSR New Redis impl.
from globals.caches import beatmaps
from objects.leaderboard import GlobalLeaderboard
from objects.score import Score
from objects.stats import Stats
from constants.modes import Mode
from constants.c_modes import CustomModes
from logger import info, error

async def drop_bmap_cache_pubsub(data: bytes) -> None:
    """
    Handles the `ussr:bmap_decache`.
    Drops the beatmap from cache. Takes in a string that is the beatmap md5.
    NOTE: This does not affect already cached leaderboards.
    """
    
    beatmaps.drop(data.decode())

async def refresh_leaderboard_pubsub(data: bytes) -> None:
    """
    Handles the `ussr:lb_refresh` pubsub.

    Data:
        beatmap_md5:mode int:custommode int
    
    Reloads the leaderboards and beatmap of an existing object alongside
    dropping the beatmap object.
    """

    # Parse pubsub data into proper variable and enums.
    md5, mode_str, c_mode_str = data.decode().split(":")
    mode = Mode(int(mode_str))
    c_mode = CustomModes(int(c_mode_str))

    # Attempts to drop beatmap regardless of its presence to stop old cached
    # being used.
    beatmaps.drop(md5)

    # Try to fetch existing leaderboard. If exists, refresh it.
    if lb := GlobalLeaderboard.from_cache(md5, c_mode, mode):
        await lb.refresh_beatmap()
        await lb.refresh()
    
    info(f"Redis Pubsub: Refreshed leaderboards and beatmap for {md5}!")

async def recalc_pp_pubsub(data: bytes) -> None:
    """
    Handles the `ussr:recalc_pp` pubsub.
    Data:
        score_id
    """

    # Get all of the required variables.
    score_id = int(data.decode())
    c_mode = CustomModes.from_score_id(score_id)

    # Attempt to fetch score.
    score = await Score.from_db(score_id, c_mode, False)
    if not score:
        error("Redis Pubsub: Error recalculating PP for score with ID: "
             f"{score_id} | Score not found!")
        return
    
    await score.calc_pp()
    await score.save_pp()
    info(f"Redis Pubsub: Recalculated PP for score {score_id}")

async def recalc_user_pubsub(data: bytes) -> None:
    """
    Handles the `ussr:recalc_user` pubsub.
    Data:
        user_id

    Recalculates the total user PP and max combo for all modes and c_modes
    and saves it within the database.
    """

    user_id = int(data.decode())

    for c_mode in CustomModes.all():
        for mode in c_mode.compatible_modes:
            st = await Stats.from_id(user_id, mode, c_mode)
            assert st is not None

            await st.calc_max_combo()
            await st.calc_pp_acc_full()
            await st.calc_playcount()
            await st.update_redis_ranks()
            await st.save()
    
    info(f"Redis Pubsub: Recalculated the statistics for user {user_id}")

# TODO: Add verify handler.
