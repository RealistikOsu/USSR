from consts.statuses import Status
from logger import error, info
from lenhttp import Request
from objects.score import Score
from objects.stats import Stats
from globs import caches
from helpers.user import restrict_user
from helpers.replays import write_replay
from copy import copy

def __pair_panel(name: str, b: str, a: str) -> str:
    """Creates a pair panel string used in score submit ranking panel.
    
    Args:
        name (str): The name of the panel.
        b (str): The before value displayed.
        a (str): The after value displayed.
    """

    return f"{name}Before:{b}|{name}After:{a}"

async def score_submit_handler(req: Request) -> str:
    """Handles the score submit endpoint for osu!"""

    print(req.body)
    print(req.files)
    print(req.post_args)
    print(req.headers)
    print(req.type)

    s = await Score.from_score_sub(req)

    if not s:
        error("Could not perform score sub! Check messages above!")
        return "error: no"
    
    if not s.bmap:
        error("Score sub failed due to no beatmap being attached.")
        return "error: no"
    
    if not s.mods.rankable():
        info("Score not submitted due to unrankable mod combo.")
        return "error: no"
    
    # TODO: Online check.
    if not caches.password.check_password(s.user_id, req.post_args["pass"]):
        return "error: pass"
    
    # Anticheat checks.
    if not req.headers.get("Token"):
        await restrict_user(s.user_id, "Tampering with osu!auth")
        return "error: ban"
    
    if req.headers.get("User-Agent") != "osu!":
        await restrict_user(s.user_id, "Score submitter.")
        return "error: ban"
    
    if s.mods.conflict():
        await restrict_user(s.user_id, "Illegal mod combo (score submitter).")
        return "error: ban"
    # TODO: version check.

    # Stats stuff
    stats = await Stats.from_sql(s.user_id, s.mode, s.c_mode)
    old_stats = copy(stats)

    # TODO: Dupe check.
    await s.submit()

    await s.bmap.increment_playcount(s.passed)

    # Stat updates
    stats.playcount += 1
    stats.total_score += s.score
    if s.bmap.status == Status.RANKED: stats.ranked_score += s.score
    if stats.max_combo < s.max_combo: stats.max_combo = s.max_combo

    await stats.recalc_pp_acc_full()
    await stats.save()

    # Write replay + anticheat.
    if (replay := req.files.get("score")) and replay != b"\r\n" and not s.passed:
        await restrict_user(s.user_id, "Score submit without replay (always "
                            "should contain it).")
        return "error: ban"
    
    if s.passed: await write_replay(s.id, replay, s.c_mode)

    info(f"User {s.user_id} has submitted a #{s.placement} {s.completed} score"
         f" on {s.bmap.song_name} +{s.mods} ({s.pp}pp)")

    # TODO: ranking panels
    return "error: no"
