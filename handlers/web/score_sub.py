from constants.complete import Completed
from constants.privileges import Privileges
from constants.statuses import Status
from constants.actions import Actions
from logger import debug, error, info, warning
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
from objects.score import Score
from objects.stats import Stats
from globals import caches
from globals import connections
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
from helpers.discord import log_first_place
from copy import copy
from config import config

def _pair_panel(name: str, b: str, a: str) -> str:
    """Creates a pair panel string used in score submit ranking panel.
    
    Args:
        name (str): The name of the panel.
        b (str): The before value displayed.
        a (str): The after value displayed.
    """

    return f"{name}Before:{b}|{name}After:{a}"

async def score_submit_handler(req: Request) -> Response:
    """Handles the score submit endpoint for osu!"""

    post_args = await req.form()

    s = await Score.from_score_sub(post_args)

    # Check if theyre online, if not, force the client to wait to log in.
    if not await check_online(s.user_id): 
        return PlainTextResponse("")

    privs = await caches.priv.get_privilege(s.user_id)
    if not s:
        error("Could not perform score sub! Check messages above!")
        return PlainTextResponse("error: no")
    
    if not s.bmap:
        error("Score sub failed due to no beatmap being attached.")
        return PlainTextResponse("error: no")
    
    if not s.mods.rankable():
        info("Score not submitted due to unrankable mod combo.")
        return PlainTextResponse("error: no")
    
    if not await caches.password.check_password(s.user_id, post_args["pass"]):
        return PlainTextResponse("error: pass")
    
    # Anticheat checks.
    if not req.headers.get("Token") and not config.CUSTOM_CLIENTS:
        await edit_user(Actions.RESTRICT, s.user_id, "Tampering with osu!auth")
        return PlainTextResponse("error: ban")
    
    if req.headers.get("User-Agent") != "osu!":
        await edit_user(Actions.RESTRICT, s.user_id, "Score submitter.")
        return PlainTextResponse("error: ban")
    
    if s.mods.conflict():
        await edit_user(Actions.RESTRICT, s.user_id, "Illegal mod combo (score submitter).")
        return PlainTextResponse("error: ban")
    # TODO: version check.

    dupe_check = await connections.sql.fetchcol( # Try to fetch as much similar score as we can.
        f"SELECT 1 FROM {s.c_mode.db_table} WHERE "
        "userid = %s AND beatmap_md5 = %s AND score = %s "
        "AND play_mode = %s AND mods = %s LIMIT 1",
        (s.user_id, s.bmap.md5, s.score, s.mode.value, s.mods.value)
    )

    if dupe_check:
        # Duplicate, just return error: no.
        warning("Duplicate score has been spotted and handled!")
        return PlainTextResponse("error: no")

    # Stats stuff
    stats = await Stats.from_id(s.user_id, s.mode, s.c_mode)
    old_stats = copy(stats)

    # Fetch old score to compare.
    prev_score = None

    if s.passed:
        debug("Fetching previous best to compare.")
        prev_db = await connections.sql.fetchone(
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
        #old_stats=old_stats, new_stats=stats
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
    replay = await post_args.getlist("score")[1].read()
    if replay and replay != b"\r\n" and not s.passed:
        await edit_user(Actions.RESTRICT, s.user_id, "Score submit without replay "
                                                     "(always should contain it).")
        return PlainTextResponse("error: ban")
    
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

    # Send webhook to discord.
    if s.placement == 1 and not privs & Privileges.USER_PUBLIC == 0:
        await log_first_place(s, old_stats, stats)
    
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
        await edit_user(Actions.RESTRICT, s.user_id, f"Surpassing PP cap as unverified! ({s.pp:.2f}pp)")
        return PlainTextResponse("error: ban")

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
        _pair_panel("rank", "0", s.placement),
        _pair_panel("maxCombo", "", s.max_combo),
        _pair_panel("accuracy", "", round(s.accuracy, 2)),
        _pair_panel("rankedScore", "", s.score),
        _pair_panel("pp", "", s.pp)
    ) if s.passed else ( # TL;DR for those of you who dont know, client requires failed panels.
        _pair_panel("rank", "0", "0"),
        _pair_panel("maxCombo", "", s.max_combo),
        _pair_panel("accuracy", "", ""),
        _pair_panel("rankedScore", "", s.score),
        _pair_panel("pp", "", "")
    )

    if s.bmap.has_leaderboard:
        # Beatmap ranking panel.
        panels.append("|".join((
            "chartId:beatmap",
            f"chartUrl:{config.SRV_URL}/beatmaps/{s.bmap.id}",
            "chartName:Beatmap Ranking",
            *(failed_not_prev_panel \
                if not prev_score or not s.passed else (
                _pair_panel("rank", prev_score.placement, s.placement),
                _pair_panel("maxCombo", prev_score.max_combo, s.max_combo),
                _pair_panel("accuracy", round(prev_score.accuracy, 2), round(s.accuracy, 2)),
                _pair_panel("rankedScore", prev_score.score, s.score),
                _pair_panel("pp", round(prev_score.pp), round(s.pp))
            )),
            f"onlineScoreId:{s.id}"
        )))

    # Overall ranking panel. XXX: Apparently unranked maps gets overall charts.
    panels.append("|".join((
        "chartId:overall",
        f"chartUrl:{config.SRV_URL}/u/{s.user_id}",
        "chartName:Global Ranking",
        *((
            _pair_panel("rank", old_stats.rank, stats.rank),
            _pair_panel("rankedScore", old_stats.ranked_score, stats.ranked_score),
            _pair_panel("totalScore", old_stats.total_score, stats.total_score),
            _pair_panel("maxCombo", old_stats.max_combo, stats.max_combo),
            _pair_panel("accuracy", round(old_stats.accuracy, 2), round(stats.accuracy, 2)),
            _pair_panel("pp", round(old_stats.pp), round(stats.pp))
        )),
        f"achievements-new:{'/'.join(new_achievements)}",
        f"onlineScoreId:{s.id}"
    )))

    return PlainTextResponse("\n".join(i for i in panels))
