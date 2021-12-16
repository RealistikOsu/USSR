from consts.complete import Completed
from consts.privileges import Privileges
from consts.statuses import Status
from consts.actions import Actions
from logger import debug, error, info, warning
from lenhttp import Request
from objects.score import Score
from objects.stats import Stats
from globs import caches
from globs import conn
from helpers.user import (
    unlock_achievement,
    get_achievements,
    edit_user,
    update_country_lb_pos,
    update_lb_pos,
)
from datetime import datetime
from helpers.replays import write_replay
from helpers.pep import check_online, stats_refresh, notify_new_score
from helpers.anticheat import surpassed_cap_restrict
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
    privs = await caches.priv.get_privilege(s.user_id)

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
        await edit_user(Actions.RESTRICT, s.user_id, "Tampering with osu!auth")
        return "error: ban"
    
    if req.headers.get("User-Agent") != "osu!":
        await edit_user(Actions.RESTRICT, s.user_id, "Score submitter.")
        return "error: ban"
    
    if s.mods.conflict():
        await edit_user(Actions.RESTRICT, s.user_id, "Illegal mod combo (score submitter).")
        return "error: ban"
    # TODO: version check.

    dupe_check = await conn.sql.fetchcol( # Try to fetch as much similar score as we can.
        f"SELECT 1 FROM {s.c_mode.db_table} WHERE "
        "userid = %s AND beatmap_md5 = %s AND score = %s "
        "AND play_mode = %s AND mods = %s LIMIT 1",
        (s.user_id, s.bmap.md5, s.score, s.mode.value, s.mods.value)
    )

    if dupe_check:
        # Duplicate, just return error: no.
        warning("Duplicate score has been spotted and handled!")
        return "error: no"

    # Stats stuff
    stats = await Stats.from_id(s.user_id, s.mode, s.c_mode)
    old_stats = copy(stats)

    # Fetch old score to compare.
    prev_score = None

    if s.passed:
        debug("Fetching previous best to compare.")
        prev_db = await conn.sql.fetchone(
            f"SELECT id FROM {stats.c_mode.db_table} WHERE userid = %s AND "
            f"beatmap_md5 = %s AND completed = 3 AND play_mode = {s.mode.value} LIMIT 1",
            (s.user_id, s.bmap.md5)
        )

        prev_score = await Score.from_db(
            prev_db[0], s.c_mode
        ) if prev_db else None

    debug("Submitting score...")
    await s.submit(
        restricted= privs & Privileges.USER_PUBLIC == 0
    )

    debug("Incrementing bmap playcount.")
    await s.bmap.increment_playcount(s.passed)


    # Stat updates
    debug("Updating stats.")
    stats.playcount += 1
    stats.total_score += s.score
    stats.total_hits += (s.count_300 + s.count_100 + s.count_50)

    add_score = s.score
    if prev_score and s.completed == Completed.BEST:
        add_score -= prev_score.score

    if s.passed and s.bmap.has_leaderboard:
        if s.bmap.status == Status.RANKED: stats.ranked_score += add_score   
        if stats.max_combo < s.max_combo: stats.max_combo = s.max_combo
        if s.completed == Completed.BEST and s.pp:
            debug("Performing PP recalculation.")
            await stats.recalc_pp_acc_full(s.pp)
    debug("Saving stats")
    await stats.save()

    # Write replay + anticheat.
    if (replay := req.files.get("score")) and replay != b"\r\n" and not s.passed:
        await edit_user(Actions.RESTRICT, s.user_id, "Score submit without replay "
                                                     "(always should contain it).")
        return "error: ban"
    
    if s.passed:
        debug("Writing replay.")
        await write_replay(s.id, replay, s.c_mode)

    info(f"User {s.username} has submitted a #{s.placement} place"
         f" on {s.bmap.song_name} +{s.mods.readable} ({round(s.pp, 2)}pp)")

    
    # Update our position on the global lbs.
    if s.completed is Completed.BEST and privs & Privileges.USER_PUBLIC\
        and old_stats.pp != stats.pp:
        debug("Updating user's global and country lb positions.")
        args = (s.user_id, round(stats.pp), s.mode, s.c_mode)
        await update_lb_pos(*args)
        await update_country_lb_pos(*args)
        await stats.update_rank()

    # Trigger peppy stats update.
    await stats_refresh(s.user_id)
    panels = []

    # At the end, check achievements.
    new_achievements = []
    if s.passed and s.bmap.has_leaderboard:
        db_achievements = await get_achievements(s.user_id)
        for ach in caches.achievements:
            if ach.id in db_achievements: continue
            if ach.cond(s, s.mode.value, stats):
                await unlock_achievement(s.user_id, ach.id)
                new_achievements.append(ach.full_name)
    
    # More anticheat checks.
    if s.completed == Completed.BEST and await surpassed_cap_restrict(s):
        await edit_user(Actions.RESTRICT, s.user_id, f"Surpassing PP cap as unverified! ({s.pp}pp)")
        return "error: ban"

    await notify_new_score(s.id)

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

    url = f"{conf.srv_url}/beatmaps/{s.bmap.id}"
    if s.bmap.has_leaderboard:
        # Beatmap ranking panel.
        panels.append("|".join((
            "chartId:beatmap",
            f"chartUrl:https://{url}/b/{s.bmap.id}",
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

    # Overall ranking panel. XXX: Apparently unranked maps gets overall charts.
    panels.append("|".join((
        "chartId:overall",
        f"chartUrl:https://{url}/u/{s.user_id}",
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
