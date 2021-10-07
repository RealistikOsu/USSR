from consts.complete import Completed
from consts.statuses import Status
from logger import debug, error, info
from lenhttp import Request
from objects.score import Score
from objects.stats import Stats
from globs import caches
from globs import conn
from helpers.user import update_rank
from datetime import datetime
from helpers.user import restrict_user, unlock_achievement
from helpers.replays import write_replay
from helpers.pep import check_online, stats_refresh
from copy import copy
from config import conf
import time
from libs.time import Timer

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

    s = await Score.from_score_sub(req)

    # Check if theyre online, if not, force the client to wait to log in.
    if not await check_online(s.user_id): return ""

    if not s:
        error("Could not perform score sub! Check messages above!")
        return "error: no"
    
    if not s.bmap:
        error("Score sub failed due to no beatmap being attached.")
        return "error: no"
    
    if not s.mods.rankable():
        info("Score not submitted due to unrankable mod combo.")
        return "error: no"
    
    if not await caches.password.check_password(s.user_id, req.post_args["pass"]):
        return "error: pass"
    
    # Anticheat checks.
    if not req.headers.get("Token") and not conf.srv_c_clients:
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
    stats = await Stats.from_id(s.user_id, s.mode, s.c_mode)
    old_stats = copy(stats)

    # Fetch old score to compare.
    scoring = "pp" if stats.c_mode.uses_ppboard else "score"
    prev_db = await conn.sql.fetchone(
        f"SELECT id FROM {stats.c_mode.db_table} WHERE userid = %s AND "
        f"beatmap_md5 = %s ORDER BY {scoring} DESC LIMIT 1",
        (s.user_id, s.bmap.md5)
    )
    prev_score = None
    if prev_db:
        prev_score = await Score.from_db(
            prev_db[0], stats.c_mode.db_table
        )

    # TODO: Dupe check.
    debug("Submitting score...")
    await s.submit()

    debug("Incrementing bmap playcount.")
    await s.bmap.increment_playcount(s.passed)

    # Stat updates
    debug("Updating stats.")
    stats.playcount += 1
    stats.total_score += s.score
    stats.total_hits += (s.count_300 + s.count_100 + s.count_50)

    add_score = s.score
    if prev_score:
        add_score -= prev_score.score

    if s.passed:
        if s.bmap.status == Status.RANKED: stats.ranked_score += add_score   
        if stats.max_combo < s.max_combo: stats.max_combo = s.max_combo
        if s.bmap.has_leaderboard and s.completed == Completed.BEST and s.pp:
            debug("Performing PP recalculation.")
            await stats.recalc_pp_acc_full(s.pp) # TODO: work out how to use bonus pp without performance loss.
    debug("Saving stats")


    # Write replay + anticheat.
    if (replay := req.files.get("score")) and replay != b"\r\n" and not s.passed:
        await restrict_user(s.user_id, "Score submit without replay (always "
                            "should contain it).")
        return "error: ban"
    
    if s.passed:
        debug("Writing replay.")
        await write_replay(s.id, replay, s.c_mode)

    info(f"User {s.user_id} has submitted a #{s.placement} place"
         f" on {s.bmap.song_name} +{s.mods.readable} ({round(s.pp, 2)}pp)")

    if not s.bmap.has_leaderboard:
        return "error: no"

    # Trigger peppy stats update.
    await stats_refresh(s.user_id)
    panels = []

    if s.passed and old_stats.pp != stats.pp:
        await update_rank(s.user_id, stats.pp, s.mode, s.c_mode)
        await stats.update_rank()

    # At the end, check achievements.
    new_achievements = []
    if s.passed:
        db_achievements = [ ach[0] for ach in await conn.sql.fetchall("SELECT achievement_id FROM users_achievements WHERE user_id = %s", (s.user_id,)) ]
        for ach in caches.achievements:
            if ach.id in db_achievements: continue
            if ach.cond(s, s.mode.value, stats):
                await unlock_achievement(s.user_id, ach.id)
                new_achievements.append(ach.full_name)

    # Create beatmap info panel.
    panels.append(
        f"beatmapId:{s.bmap.id}|"
        f"beatmapSetId:{s.bmap.set_id}|"
        f"beatmapPlaycount:{s.bmap.playcount}|"
        f"beatmapPasscount:{s.bmap.passcount}|"
        f"approvedDate:{datetime.utcfromtimestamp(s.bmap.last_update).strftime('%Y-%m-%d %H:%M:%S')}"
    )

    failed_not_prev_panel = (
        __pair_panel("rank", "0", s.placement),
        __pair_panel("maxCombo", "", s.max_combo),
        __pair_panel("accuracy", "", round(s.accuracy, 2)),
        __pair_panel("rankedScore", "", s.score),
        __pair_panel("pp", "", s.pp)
    ) if s.passed else ( # TL;DR for those of you who dont know, client requires failed panels.
        __pair_panel("rank", "0", "0"),
        __pair_panel("maxCombo", "", s.max_combo),
        __pair_panel("accuracy", "", ""),
        __pair_panel("rankedScore", "", s.score),
        __pair_panel("pp", "", "")
    )

    # Beatmap ranking panel.
    panels.append("|".join((
        "chartId:beatmap",
        f"chartUrl:https://osu.ppy.sh/beatmaps/{s.bmap.id}", # TODO: Replace it with our own domain.
        "chartName:Beatmap Ranking",
        *(failed_not_prev_panel \
            if not prev_score or not s.passed else (
            __pair_panel("rank", prev_score.placement, s.placement),
            __pair_panel("maxCombo", prev_score.max_combo, s.max_combo),
            __pair_panel("accuracy", round(prev_score.accuracy, 2), round(s.accuracy, 2)),
            __pair_panel("rankedScore", prev_score.score, s.score),
            __pair_panel("pp", round(prev_score.pp), round(s.pp))
        )),
        f"onlineScoreId:{s.id}"
    )))

    # Overall ranking panel.
    panels.append("|".join((
        "chartId:overall",
        f"chartUrl:https://osu.ppy.sh/users/{s.user_id}", # TODO: Replace it with our own domain.
        "chartName:Global Ranking",
        *((
            __pair_panel("rank", old_stats.rank, stats.rank),
            __pair_panel("rankedScore", old_stats.ranked_score, stats.ranked_score),
            __pair_panel("totalScore", old_stats.total_score, stats.total_score),
            __pair_panel("maxCombo", old_stats.max_combo, stats.max_combo),
            __pair_panel("accuracy", round(old_stats.accuracy, 2), round(stats.accuracy, 2)),
            __pair_panel("pp", round(old_stats.pp), round(stats.pp))
        )),
        f"achievements-new:{'/'.join(new_achievements)}",
        f"onlineScoreId:{s.id}"
    )))

    return "\n".join(i for i in panels)
