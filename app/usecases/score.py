from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Optional

import app.state
import app.usecases
import app.utils
from app.models.achievement import Achievement
from app.models.beatmap import Beatmap
from app.models.score import Score
from app.models.stats import Stats
from app.models.user import User
from app.objects.binary import BinaryWriter


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
    else:
        raise NotImplementedError(f"Unknown mode: {vanilla_mode}")


async def unlock_achievements(score: Score, stats: Stats) -> list[Achievement]:
    new_achievements: list[Achievement] = []

    user_achievements = await app.usecases.user.fetch_achievements(
        score.user_id,
        score.mode,
    )
    for achievement in app.state.cache.ACHIEVEMENTS:
        if achievement.id in user_achievements:
            continue

        if achievement.cond(score, score.mode.as_vn, stats):
            new_achievements.append(achievement)

            # db insertion is not required immediately, let's run it in the bg!
            asyncio.create_task(
                app.usecases.user.unlock_achievement(
                    achievement.id,
                    score.user_id,
                    score.mode,
                ),
            )

    return new_achievements


async def handle_first_place(
    score: Score,
    beatmap: Beatmap,
    user: User,
) -> None:
    await app.state.services.database.execute(
        "DELETE FROM scores_first WHERE beatmap_md5 = :md5 AND mode = :mode AND rx = :rx",
        {"md5": score.map_md5, "mode": score.mode.as_vn, "rx": score.mode.relax_int},
    )

    await app.state.services.database.execute(
        (
            "INSERT INTO scores_first (beatmap_md5, mode, rx, scoreid, userid) VALUES "
            "(:md5, :mode, :rx, :sid, :uid)"
        ),
        {
            "md5": score.map_md5,
            "mode": score.mode.as_vn,
            "rx": score.mode.relax_int,
            "sid": score.id,
            "uid": score.user_id,
        },
    )

    msg = f"[{score.mode.relax_str}] User {user.embed} has submitted a #1 place on {beatmap.embed} +{score.mods!r} ({score.pp:.2f}pp)"
    await app.utils.send_announcement_as_side_effect(msg)


OSU_VERSION = 2021_11_03


async def build_full_replay(score: Score) -> Optional[BinaryWriter]:
    replay_bytes = await app.usecases.replays.download_replay(score.id)

    if replay_bytes is None:
        # TODO: assert the error code is "not found"?
        logging.error(
            f"Requested replay ID {score.id}, but no file could be found",
        )
        return

    username = await app.usecases.usernames.get_username(score.user_id)
    if not username:
        return

    replay_md5 = hashlib.md5(
        "{}p{}o{}o{}t{}a{}r{}e{}y{}o{}u{}{}{}".format(
            score.n100 + score.n300,
            score.n50,
            score.ngeki,
            score.nkatu,
            score.nmiss,
            score.map_md5,
            score.max_combo,
            "true" if score.full_combo else "false",
            username,
            score.score,
            0,
            score.mods.value,
            "true",
        ).encode(),
    ).hexdigest()

    return (
        BinaryWriter()
        .write_u8_le(score.mode.as_vn)
        .write_i32_le(OSU_VERSION)
        .write_osu_string(score.map_md5)
        .write_osu_string(username)
        .write_osu_string(replay_md5)
        .write_i16_le(score.n300)
        .write_i16_le(score.n100)
        .write_i16_le(score.n50)
        .write_i16_le(score.ngeki)
        .write_i16_le(score.nkatu)
        .write_i16_le(score.nmiss)
        .write_i32_le(score.score)
        .write_i16_le(score.max_combo)
        .write_u8_le(score.full_combo)
        .write_i32_le(score.mods.value)
        .write_u8_le(0)
        .write_i64_le(app.utils.ts_to_utc_ticks(score.time))
        .write_i32_le(len(replay_bytes))
        .write_raw(replay_bytes)
        .write_i64_le(score.id)
    )
