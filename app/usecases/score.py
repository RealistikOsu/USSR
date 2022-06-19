from __future__ import annotations

import asyncio

import app.state
import app.usecases
import app.utils
from app.constants.mods import Mods
from app.constants.score_status import ScoreStatus
from app.models.beatmap import Beatmap
from app.models.score import Score
from app.models.stats import Stats
from app.models.user import User


def calculate_accuracy(score: Score) -> float:
    vanilla_mode = score.mode.as_vn

    n300 = score.n300
    n100 = score.n100
    n50 = score.n50

    ngeki = score.ngeki
    nkatu = score.nkatu

    nmiss = score.nmiss

    if vanilla_mode == 0:  # osu!
        total = n300 + n100 + n50 + nmiss

        if total == 0:
            return 0.0

        return (
            100.0 * ((n300 * 300.0) + (n100 * 100.0) + (n50 * 50.0)) / (total * 300.0)
        )

    elif vanilla_mode == 1:  # osu!taiko
        total = n300 + n100 + nmiss

        if total == 0:
            return 0.0

        return 100.0 * ((n100 * 0.5) + n300) / total

    elif vanilla_mode == 2:  # osu!catch
        total = n300 + n100 + n50 + nkatu + nmiss

        if total == 0:
            return 0.0

        return 100.0 * (n300 + n100 + n50) / total

    elif vanilla_mode == 3:  # osu!mania
        total = n300 + n100 + n50 + ngeki + nkatu + nmiss

        if total == 0:
            return 0.0

        return (
            100.0
            * (
                (n50 * 50.0)
                + (n100 * 100.0)
                + (nkatu * 200.0)
                + ((n300 + ngeki) * 300.0)
            )
            / (total * 300.0)
        )


def calculate_status(score: Score) -> None:
    if score.old_best:
        if score.pp > score.old_best.pp:
            score.status = ScoreStatus.BEST
            score.old_best.status = ScoreStatus.SUBMITTED
        elif score.pp == score.old_best.pp and score.score > score.old_best.score:
            # spin to win!
            score.status = ScoreStatus.BEST
            score.old_best.status = ScoreStatus.SUBMITTED
        else:
            score.status = ScoreStatus.SUBMITTED
    else:
        score.status = ScoreStatus.BEST


async def unlock_achievements(score: Score, stats: Stats) -> list[str]:
    new_achievements: list[str] = []

    user_achievements = await app.usecases.user.fetch_achievements(score.user_id)
    for achievement in app.state.cache.ACHIEVEMENTS:
        if achievement.id in user_achievements:
            continue

        if achievement.cond(score, score.mode.as_vn, stats):
            new_achievements.append(achievement.full_name)

            # db insertion is not required immediately, let's run it in the bg!
            asyncio.create_task(
                app.usecases.user.unlock_achievement(score.user_id, achievement.id),
            )

    return new_achievements


def get_non_computed_playtime(score: Score, beatmap: Beatmap) -> int:
    if score.passed:
        return beatmap.hit_length

    return score.time_elapsed // 1000


def get_computed_playtime(score: Score, beatmap: Beatmap) -> int:
    if score.passed:
        return beatmap.hit_length

    value = score.time_elapsed
    if score.mods & Mods.DOUBLETIME:
        value //= 1.5
    elif score.mods & Mods.HALFTIME:
        value //= 0.75

    if beatmap.hit_length and value > beatmap.hit_length * 1.33:
        return 0

    return value


async def handle_first_place(
    score: Score,
    beatmap: Beatmap,
    user: User,
    old_stats: Stats,
    new_stats: Stats,
) -> None:
    await app.state.services.database.execute(
        "DELETE FROM first_places WHERE beatmap_md5 = :md5 AND mode = :mode AND relax = :rx",
        {"md5": score.map_md5, "mode": score.mode.value, "relax": score.mode.relax_int},
    )

    await app.state.services.database.execute(
        (
            "INSERT INTO first_places (score_id, user_id, score, max_combo, full_combo, "
            "mods, 300_count, 100_count, 50_count, ckatus_count, cgekis_count, miss_count, "
            "timestamp, mode, completed, accuracy, pp, play_time, beatmap_md5, relax) VALUES "
            "(:score_id, :user_id, :score, :max_combo, :full_combo, "
            ":mods, :300_count, :100_count, :50_count, :ckatus_count, :cgekis_count, :miss_count, "
            ":timestamp, :mode, :completed, :accuracy, :pp, :play_time, :beatmap_md5, :relax)"
        ),
        {
            "score_id": score.id,
            "user_id": score.user_id,
            "score": score.score,
            "max_combo": score.max_combo,
            "full_combo": score.full_combo,
            "mods": score.mods.value,
            "300_count": score.n300,
            "100_count": score.n100,
            "50_count": score.n50,
            "ckatus_count": score.nkatu,
            "cgekis_count": score.ngeki,
            "miss_count": score.nmiss,
            "timestamp": score.time,
            "mode": score.mode.as_vn,
            "completed": score.status.value,
            "accuracy": score.acc,
            "play_time": score.time,
            "beatmap_md5": score.map_md5,
            "relax": score.mode.relax_int,
        },
    )

    msg = f"[{score.mode.relax_str}] User {user.embed} has submitted a #1 place on {beatmap.embed} +{score.mods!r} ({score.pp:.2f}pp)"
    await app.utils.announce(msg)

    await app.usecases.discord.log_first_place(
        score,
        user,
        beatmap,
        old_stats,
        new_stats,
    )
