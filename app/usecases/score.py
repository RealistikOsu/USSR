from __future__ import annotations

import hashlib

import app.state
import app.usecases
from app import job_scheduling
from app.models.achievement import Achievement
from app.models.beatmap import Beatmap
from app.models.score import Score
from app.models.stats import Stats
from app.models.user import User
from app.objects.binary import BinaryWriter
from app.utils.datetime import timestamp_to_dotnet_ticks


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
            await app.usecases.user.unlock_achievement(
                achievement.id,
                score.user_id,
                score.mode,
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
    job_scheduling.schedule_job(
        app.usecases.chat.send_message_to_channel("#announce", msg),
    )


OSU_VERSION = 2021_11_03


async def build_full_replay(score: Score) -> BinaryWriter | None:
    replay_bytes = await app.usecases.replays.download_replay(score.id)

    if replay_bytes is None:
        return None

    username = await app.usecases.usernames.get_username(score.user_id)
    if username is None:
        return None

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
        .write_i64_le(timestamp_to_dotnet_ticks(score.time))
        .write_i32_le(len(replay_bytes))
        .write_raw(replay_bytes)
        .write_i64_le(score.id)
    )
