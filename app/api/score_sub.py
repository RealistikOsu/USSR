from __future__ import annotations

import asyncio
import hashlib
import os
import time
from base64 import b64decode
from copy import copy
from datetime import datetime
from typing import NamedTuple
from typing import Optional
from typing import TypeVar
from typing import Union

from fastapi import File
from fastapi import Form
from fastapi import Header
from fastapi import Request
from fastapi.datastructures import FormData
from py3rijndael import Pkcs7Padding
from py3rijndael import RijndaelCbc
from starlette.datastructures import UploadFile as StarletteUploadFile

import app.state
import app.usecases
import app.utils
import logger
from app.constants.mode import Mode
from app.constants.ranked_status import RankedStatus
from app.constants.score_status import ScoreStatus
from app.models.score import Score
from app.objects.path import Path
from app.usecases.user import restrict_user
from config import config


class ScoreData(NamedTuple):
    score_data_b64: bytes
    replay_file: StarletteUploadFile


async def parse_form(score_data: FormData) -> Optional[ScoreData]:
    try:
        score_parts = score_data.getlist("score")
        assert len(score_parts) == 2, "Invalid score data"

        score_data_b64 = score_data.getlist("score")[0]
        assert isinstance(score_data_b64, str), "Invalid score data"
        replay_file = score_data.getlist("score")[1]
        assert isinstance(replay_file, StarletteUploadFile), "Invalid replay data"
    except AssertionError as exc:
        logger.warning(f"Failed to validate score multipart data: ({exc.args[0]})")
        return None
    else:
        return (
            score_data_b64.encode(),
            replay_file,
        )


class ScoreClientData(NamedTuple):
    score_data: list[str]
    client_hash_decoded: str


def decrypt_score_data(
    score_data_b64: bytes,
    client_hash_b64: bytes,
    iv_b64: bytes,
    osu_version: str,
) -> tuple[list[str], str]:
    aes = RijndaelCbc(
        key=f"osu!-scoreburgr---------{osu_version}".encode(),
        iv=b64decode(iv_b64),
        padding=Pkcs7Padding(32),
        block_size=32,
    )

    score_data = aes.decrypt(b64decode(score_data_b64)).decode().split(":")
    client_hash_decoded = aes.decrypt(b64decode(client_hash_b64)).decode()

    return score_data, client_hash_decoded


DATA_PATH = Path(config.data_dir)
MAPS_PATH = DATA_PATH / "maps"


T = TypeVar("T", bound=Union[int, float])


def chart_entry(name: str, before: Optional[T], after: T) -> str:
    return f"{name}Before:{before or ''}|{name}After:{after}"


async def submit_score(
    request: Request,
    token: Optional[str] = Header(None),
    user_agent: str = Header(...),
    exited_out: bool = Form(..., alias="x"),
    fail_time: int = Form(..., alias="ft"),
    visual_settings_b64: bytes = Form(..., alias="fs"),
    updated_beatmap_hash: str = Form(..., alias="bmk"),
    storyboard_md5: Optional[str] = Form(None, alias="sbk"),
    iv_b64: bytes = Form(..., alias="iv"),
    unique_ids: str = Form(..., alias="c1"),
    score_time: int = Form(..., alias="st"),
    password_md5: str = Form(..., alias="pass"),
    osu_version: str = Form(..., alias="osuver"),
    client_hash_b64: bytes = Form(..., alias="s"),
    fl_cheat_screenshot: Optional[bytes] = File(None, alias="i"),
):
    start = time.perf_counter_ns()

    score_params = await parse_form(await request.form())
    if not score_params:
        return

    score_data_b64, replay_file = score_params
    score_data, _ = decrypt_score_data(
        score_data_b64,
        client_hash_b64,
        iv_b64,
        osu_version,
    )

    username = score_data[1].rstrip()
    if not (user := await app.usecases.user.auth_user(username, password_md5)):
        return  # empty resp tells osu to retry

    beatmap_md5 = score_data[0]
    if not (beatmap := await app.usecases.beatmap.fetch_by_md5(beatmap_md5)):
        return b"error: beatmap"

    score = Score.from_submission(score_data[2:], beatmap_md5, user)
    leaderboard = await app.usecases.leaderboards.fetch(beatmap, score.mode)

    score.acc = app.usecases.score.calculate_accuracy(score)
    score.quit = exited_out

    await app.usecases.user.update_latest_activity(user.id)

    if not score.mods.rankable:
        return b"error: no"

    if not token and not config.custom_clients:
        await app.usecases.user.restrict_user(
            user,
            "Tampering with osu!auth.",
            "The client has not sent an anticheat token to the server, meaning "
            "that they either have disabled the anticheat, or are using a custom/older "
            "client. (score submit gate)",
        )

    if user_agent != "osu!":
        await app.usecases.user.restrict_user(
            user,
            "Score submitter or other external client behaviour emulator",
            "The expected user-agent header for an osu! client is 'osu!', while "
            f"the client sent '{user_agent}'. (score submit gate)",
        )

    if score.mods.conflict:
        await app.usecases.user.restrict_user(
            user,
            "Illegal score mod combination.",
            "The user attempted to submit a score with the mod combination "
            f"+{score.mods!r}, which contains mutually exclusive/illegal mods. "
            "(score submit gate)",
        )

    osu_file_path = MAPS_PATH / f"{beatmap.id}.osu"
    if await app.usecases.performance.check_local_file(
        osu_file_path,
        beatmap.id,
        beatmap.md5,
    ):
        app.usecases.performance.calculate_score(score, osu_file_path)

        if score.passed:
            old_best = await leaderboard.find_user_score(user.id)

            if old_best:
                score.old_best = old_best["score"]

                if score.old_best:
                    score.old_best.rank = old_best["rank"]

            app.usecases.score.calculate_status(score)
        elif score.quit:
            score.status = ScoreStatus.QUIT
        else:
            score.status = ScoreStatus.FAILED

    score.time_elapsed = score_time if score.passed else fail_time

    if await app.state.services.database.fetch_val(
        (
            f"SELECT 1 FROM {score.mode.scores_table} WHERE userid = :id AND beatmap_md5 = :md5 AND score = :score "
            "AND play_mode = :mode AND mods = :mods"
        ),
        {
            "id": user.id,
            "md5": beatmap.md5,
            "score": score.score,
            "mode": score.mode.as_vn,
            "mods": score.mods.value,
        },
    ):
        # duplicate score detected
        return b"error: no"

    if (
        beatmap.gives_pp
        and score.pp > score.mode.pp_cap
        and not await app.usecases.verified.get_verified(user.id)
    ):
        await restrict_user(
            user,
            f"Surpassing PP cap as unverified!",
            "The user attempted to submit a score with PP higher than the "
            f"PP cap. {beatmap.song_name} +{score.mods!r} ({score.pp:.2f}pp)"
            f" ID: {score.id} (score submit gate)",
        )

    if score.status == ScoreStatus.BEST:
        await app.state.services.database.execute(
            f"UPDATE {score.mode.scores_table} SET completed = 2 WHERE completed = 3 AND beatmap_md5 = :md5 AND userid = :id AND play_mode = :mode",
            {"md5": beatmap.md5, "id": user.id, "mode": score.mode.as_vn},
        )

    score.id = await app.state.services.database.execute(
        (
            f"INSERT INTO {score.mode.scores_table} (beatmap_md5, userid, score, max_combo, full_combo, mods, 300_count, 100_count, 50_count, katus_count, "
            "gekis_count, misses_count, time, play_mode, completed, accuracy, pp, playtime) VALUES "
            "(:beatmap_md5, :userid, :score, :max_combo, :full_combo, :mods, :300_count, :100_count, :50_count, :katus_count, "
            ":gekis_count, :misses_count, :time, :play_mode, :completed, :accuracy, :pp, :playtime)"
        ),
        score.db_dict,
    )

    if score.passed:
        replay_data = await replay_file.read()

        replay_path = app.utils.VANILLA_REPLAYS
        if score.mode.relax:
            replay_path = app.utils.RELAX_REPLAYS

        if score.mode.autopilot:
            replay_path = app.utils.AUTOPILOT_REPLAYS

        if len(replay_data) < 24:
            await restrict_user(
                user,
                "Score submit without replay.",
                "The user attempted to submit a completed score without a replay "
                "attached. This should NEVER happen and means they are likely using "
                "a replay editor. (score submit gate)",
            )
        else:
            replay_file = replay_path / f"replay_{score.id}.osr"
            replay_file.write_bytes(replay_data)

    asyncio.create_task(app.usecases.beatmap.increment_playcount(beatmap))
    asyncio.create_task(app.usecases.user.increment_playtime(score, beatmap))

    stats = await app.usecases.stats.fetch(user.id, score.mode)
    old_stats = copy(stats)

    stats.playcount += 1
    stats.total_score += score.score
    stats.total_hits += score.n300 + score.n100 + score.n50

    if score.passed and beatmap.has_leaderboard:
        if beatmap.status == RankedStatus.RANKED:
            stats.ranked_score += score.score

            if score.old_best and score.status == ScoreStatus.BEST:
                stats.ranked_score -= score.old_best.score

        if stats.max_combo < score.max_combo:
            stats.max_combo = score.max_combo

        if score.status == ScoreStatus.BEST and score.pp:
            await app.usecases.stats.full_recalc(stats, score.pp)

            await leaderboard.add_score(score)

    await app.usecases.stats.save(stats)

    if (
        score.status == ScoreStatus.BEST
        and not user.privileges.is_restricted
        and old_stats.pp != stats.pp
    ):
        await app.usecases.stats.update_rank(stats)

    await app.usecases.stats.refresh_stats(user.id)

    if score.status == ScoreStatus.BEST:
        score.rank = await leaderboard.find_score_rank(score.user_id, score.id)
    elif score.status == ScoreStatus.SUBMITTED:
        score.rank = await leaderboard.whatif_placement(
            user.id,
            score.pp if score.mode > Mode.MANIA else score.score,
        )

    if (
        score.rank == 1
        and score.status == ScoreStatus.BEST
        and beatmap.has_leaderboard
        and not user.privileges.is_restricted
    ):
        asyncio.create_task(
            app.usecases.score.handle_first_place(
                score,
                beatmap,
                user,
                old_stats,
                stats,
            ),
        )

    asyncio.create_task(app.utils.notify_new_score(score.id))

    if score.old_best:
        beatmap_ranking_chart = (
            chart_entry("rank", score.old_best.rank, score.rank),
            chart_entry("rankedScore", score.old_best.score, score.score),
            chart_entry("totalScore", score.old_best.score, score.score),
            chart_entry("maxCombo", score.old_best.max_combo, score.max_combo),
            chart_entry("accuracy", round(score.old_best.acc, 2), round(score.acc, 2)),
            chart_entry("pp", round(score.old_best.pp, 2), round(score.pp, 2)),
        )
    else:
        beatmap_ranking_chart = (
            chart_entry("rank", None, score.rank),
            chart_entry("rankedScore", None, score.score),
            chart_entry("totalScore", None, score.score),
            chart_entry("maxCombo", None, score.max_combo),
            chart_entry("accuracy", None, round(score.acc, 2)),
            chart_entry("pp", None, round(score.pp, 2)),
        )

    overall_ranking_chart = (
        chart_entry("rank", old_stats.rank, stats.rank),
        chart_entry("rankedScore", old_stats.ranked_score, stats.ranked_score),
        chart_entry("totalScore", old_stats.total_score, stats.total_score),
        chart_entry("maxCombo", old_stats.max_combo, stats.max_combo),
        chart_entry("accuracy", round(old_stats.accuracy, 2), round(stats.accuracy, 2)),
        chart_entry("pp", old_stats.pp, stats.pp),
    )

    new_achievements: list[str] = []
    if score.passed and beatmap.has_leaderboard and not user.privileges.is_restricted:
        new_achievements = await app.usecases.score.unlock_achievements(score, stats)

    achievements_str = "/".join(new_achievements)

    submission_charts = [
        f"beatmapId:{beatmap.id}",
        f"beatmapSetId:{beatmap.set_id}",
        f"beatmapPlaycount:{beatmap.plays}",
        f"beatmapPasscount:{beatmap.passes}",
        f"approvedDate:{datetime.utcfromtimestamp(beatmap.last_update).strftime('%Y-%m-%d %H:%M:%S')}",
        "\n",
        "chartId:beatmap",
        f"chartUrl:{beatmap.set_url}",
        "chartName:Beatmap Ranking",
        *beatmap_ranking_chart,
        f"onlineScoreId:{score.id}",
        "\n",
        "chartId:overall",
        f"chartUrl:{user.url}",
        "chartName:Overall Ranking",
        *overall_ranking_chart,
        f"achievements-new:{achievements_str}",
    ]

    end = time.perf_counter_ns()
    formatted_time = app.utils.format_time(end - start)
    logger.info(
        f"{user} submitted a {score.pp:.2f}pp {score.mode!r} score on {beatmap.song_name} in {formatted_time}",
    )

    return "|".join(submission_charts).encode()
