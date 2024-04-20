from __future__ import annotations

import dataclasses
import hashlib
import logging
import time
from base64 import b64decode
from base64 import b64encode
from copy import copy
from datetime import datetime
from typing import NamedTuple
from typing import Optional
from typing import TypeVar
from typing import Union

import aio_pika
import orjson
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
import config
from app import job_scheduling
from app.adapters import amplitude
from app.constants.mode import Mode
from app.constants.ranked_status import RankedStatus
from app.constants.score_status import ScoreStatus
from app.models.achievement import Achievement
from app.models.score import Score
from app.models.score_submission_request import ScoreSubmissionRequest
from app.objects.path import Path
from app.redis_lock import RedisLock
from app.usecases.user import restrict_user


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
        logging.warning(f"Failed to validate score multipart data: ({exc.args[0]})")
        return None
    else:
        return ScoreData(
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
    start = time.perf_counter()

    score_params = await parse_form(await request.form())
    if not score_params:
        return b"error: no"

    score_data_b64, replay_file = score_params
    score_data, _ = decrypt_score_data(
        score_data_b64,
        client_hash_b64,
        iv_b64,
        osu_version,
    )

    beatmap_md5 = score_data[0]
    if not (beatmap := await app.usecases.beatmap.fetch_by_md5(beatmap_md5)):
        return b"error: beatmap"

    username = score_data[1].rstrip()
    if not (user := await app.usecases.user.auth_user(username, password_md5)):
        return b""  # empty resp tells osu to retry

    score = Score.from_submission(score_data[2:], beatmap_md5, user)
    leaderboard = await app.usecases.leaderboards.fetch_beatmap_leaderboard(
        beatmap,
        score.mode,
        requestee_user_id=user.id,
    )
    previous_best = leaderboard.personal_best

    score.acc = app.usecases.score.calculate_accuracy(score)
    score.quit = exited_out

    await app.usecases.user.update_latest_activity(user.id)

    if not score.mods.rankable:
        return b"error: no"

    # TODO: fix osu updates making this check useless?
    # if not token and not config.ALLOW_CUSTOM_CLIENTS:
    #     await app.usecases.user.restrict_user(
    #         user,
    #         "The client has not sent an anticheat token to the server, meaning "
    #         "that they either have disabled the anticheat, or are using a custom/older "
    #         "client. (score submit gate)",
    #     )

    if user_agent != "osu!":
        await app.usecases.user.restrict_user(
            user,
            "The expected user-agent header for an osu! client is 'osu!', while "
            f"the client sent '{user_agent}'. (score submit gate)",
        )
    await app.usecases.user.handle_pending_username_change(user.id)

    if score.mods.conflict:
        await app.usecases.user.restrict_user(
            user,
            "The user attempted to submit a score with the mod combination "
            f"+{score.mods!r}, which contains mutually exclusive/illegal mods. "
            "(score submit gate)",
        )

    async with RedisLock(f"score_submission:{score.online_checksum}"):
        score_exists = (
            await app.state.services.database.fetch_val(
                f"SELECT 1 FROM {score.mode.scores_table} WHERE checksum = :checksum",
                {"checksum": score.online_checksum},
            )
        ) is not None

        if score_exists:
            return b"error: no"

        score.pp, score.sr = await app.usecases.performance.calculate_performance(
            beatmap.id,
            score.mode,
            score.mods.value,
            score.max_combo,
            score.acc,
            score.nmiss,
        )

        # calculate the score's status
        if score.passed:
            if previous_best is not None:
                if score.pp > previous_best["pp"]:
                    score.status = ScoreStatus.BEST
                elif (
                    score.pp == previous_best["pp"]
                    and score.score > previous_best["score"]
                ):
                    # spin to win!
                    score.status = ScoreStatus.BEST
                else:
                    score.status = ScoreStatus.SUBMITTED
            else:
                score.status = ScoreStatus.BEST
        elif score.quit:
            score.status = ScoreStatus.QUIT
        else:
            score.status = ScoreStatus.FAILED

        score.time_elapsed = score_time if score.passed else fail_time

        if score.status == ScoreStatus.BEST:
            await app.state.services.database.execute(
                f"""\
                UPDATE {score.mode.scores_table}
                   SET completed = 2
                 WHERE completed = 3
                   AND beatmap_md5 = :beatmap_md5
                   AND userid = :userid
                   AND play_mode = :mode
                """,
                {
                    "beatmap_md5": beatmap.md5,
                    "userid": user.id,
                    "mode": score.mode.as_vn,
                },
            )

        score.id = await app.state.services.database.execute(
            (
                # TODO: add playtime
                f"INSERT INTO {score.mode.scores_table} (beatmap_md5, userid, score, max_combo, full_combo, mods, 300_count, 100_count, 50_count, katus_count, "
                "gekis_count, misses_count, time, play_mode, completed, accuracy, pp, checksum) VALUES "
                "(:beatmap_md5, :userid, :score, :max_combo, :full_combo, :mods, :300_count, :100_count, :50_count, :katus_count, "
                ":gekis_count, :misses_count, :time, :play_mode, :completed, :accuracy, :pp, :checksum)"
            ),
            score.db_dict,
        )

    replay_data = await replay_file.read()

    if score.passed:
        submission_request = dataclasses.asdict(
            ScoreSubmissionRequest(
                score_data=score_data_b64.decode(),
                exited_out=exited_out,
                fail_time=fail_time,
                visual_settings_b64=visual_settings_b64.decode(),
                updated_beatmap_hash=updated_beatmap_hash,
                storyboard_md5=storyboard_md5,
                iv_b64=iv_b64.decode(),
                unique_ids=unique_ids,
                score_time=score_time,
                osu_version=osu_version,
                client_hash_b64=client_hash_b64.decode(),
                replay_data_b64=b64encode(replay_data).decode(),
                score_id=score.id,
                user_id=user.id,
                osu_auth_token=token,
                mode_vn=score.mode.as_vn,
                relax=score.mode.relax_int,
            ),
        )

        # send request to rmq
        if app.state.services.amqp_channel is not None:
            for routing_key in config.SCORE_SUBMISSION_ROUTING_KEYS:
                await app.state.services.amqp_channel.default_exchange.publish(
                    aio_pika.Message(body=orjson.dumps(submission_request)),
                    routing_key=routing_key,
                )

    # update most played
    await app.state.services.database.execute(
        """\
        INSERT INTO user_beatmaps (userid, map, rx, mode, count)
        VALUES (:uid, :md5, :rx, :mode, 1)
        ON DUPLICATE KEY UPDATE count = count + 1
        """,
        {
            "uid": user.id,
            "md5": score.map_md5,
            "rx": score.mode.relax_int,
            "mode": score.mode.as_vn,
        },
    )

    if (
        beatmap.gives_pp
        and score.pp > await app.usecases.pp_cap.get_pp_cap(score.mode, score.mods)
        and not await app.usecases.whitelist.get_whitelisted(user.id, score.mode)
        and score.passed
    ):
        await restrict_user(
            user,
            "The user attempted to submit a score with PP higher than the "
            f"PP cap. {beatmap.song_name} +{score.mods!r} ({score.pp:.2f}pp)"
            f" ID: {score.id} (score submit gate)",
        )

    if score.passed:
        if len(replay_data) < 24:
            await restrict_user(
                user,
                "The user attempted to submit a completed score without a replay "
                "attached. This should NEVER happen and means they are likely using "
                "a replay editor. (score submit gate)",
            )
        else:
            await app.usecases.replays.save_replay(score.id, replay_data)

    stats = await app.usecases.stats.fetch(user.id, score.mode)
    if stats is None:
        return b"error: no"

    old_stats = copy(stats)

    total_hits = score.n300 + score.n100
    if score.mode.as_vn != Mode.CATCH:
        total_hits += score.n50

    if score.mode.as_vn in (Mode.TAIKO, Mode.MANIA):
        total_hits += score.ngeki + score.nkatu

    stats.playcount += 1
    stats.playtime += score.time_elapsed // 1000
    stats.total_score += score.score
    stats.total_hits += total_hits

    if score.passed and beatmap.has_leaderboard:
        if stats.max_combo < score.max_combo:
            stats.max_combo = score.max_combo

        if score.pp:
            await app.usecases.stats.full_recalc(stats, score.pp)

        if (
            beatmap.status in (RankedStatus.RANKED, RankedStatus.APPROVED)
            and score.status == ScoreStatus.BEST
        ):
            stats.ranked_score += score.score

            if previous_best is not None:
                stats.ranked_score -= previous_best["score"]

    await app.usecases.stats.save(stats)

    if (
        score.status == ScoreStatus.BEST
        and not user.privileges.is_restricted
        and old_stats.pp != stats.pp
    ):
        await app.usecases.user.update_latest_pp_awarded(user.id, score.mode)
        await app.usecases.stats.update_rank(stats)

    await app.usecases.stats.refresh_stats(user.id)

    score.rank = await app.usecases.leaderboards.find_score_rank(
        score_id_to_judge=score.id,
        beatmap_md5=beatmap.md5,
        user_id=score.user_id,
        mode=score.mode,
    )

    if (
        score.rank == 1
        and score.status == ScoreStatus.BEST
        and beatmap.has_leaderboard
        and not user.privileges.is_restricted
    ):
        await app.usecases.score.handle_first_place(
            score,
            beatmap,
            user,
        )

    # NOTE: osu! login double hashes with md5, while score submission
    # only hashes it a single time. we perform the second hashing here.
    uninstall_id, disk_id = unique_ids.split("|", maxsplit=1)
    login_disk_id = hashlib.md5(disk_id.encode()).hexdigest()
    if login_disk_id == "dcfcd07e645d245babe887e5e2daa016":
        # NOTE: this is the result of `md5(md5("0"))`.
        # The osu! client will send this sometimes because WMI
        # may return a "0" as the disk serial number if a hardware
        # manufacturer has not set one.
        # (disk signature is optional but serial number is required)
        device_id = None
    else:
        device_id = hashlib.sha1(login_disk_id.encode()).hexdigest()

    if config.AMPLITUDE_API_KEY:
        job_scheduling.schedule_job(
            amplitude.track(
                event_name="score_submission",
                user_id=str(user.id),
                device_id=device_id,
                event_properties={
                    "beatmap": amplitude.format_beatmap(beatmap),
                    "score": amplitude.format_score(score),
                    "user": amplitude.format_user(user),
                },
            ),
        )

    if previous_best is not None:
        beatmap_ranking_chart = (
            chart_entry("rank", previous_best["score_rank"], score.rank),
            chart_entry("rankedScore", previous_best["score"], score.score),
            chart_entry("totalScore", previous_best["score"], score.score),
            chart_entry("maxCombo", previous_best["max_combo"], score.max_combo),
            chart_entry(
                "accuracy",
                round(previous_best["accuracy"], 2),
                round(score.acc, 2),
            ),
            chart_entry("pp", round(previous_best["pp"]), round(score.pp)),
        )
    else:
        beatmap_ranking_chart = (
            chart_entry("rank", None, score.rank),
            chart_entry("rankedScore", None, score.score),
            chart_entry("totalScore", None, score.score),
            chart_entry("maxCombo", None, score.max_combo),
            chart_entry("accuracy", None, round(score.acc, 2)),
            chart_entry("pp", None, round(score.pp)),
        )

    overall_ranking_chart = (
        chart_entry("rank", old_stats.rank, stats.rank),
        chart_entry("rankedScore", old_stats.ranked_score, stats.ranked_score),
        chart_entry("totalScore", old_stats.total_score, stats.total_score),
        chart_entry("maxCombo", old_stats.max_combo, stats.max_combo),
        chart_entry("accuracy", round(old_stats.accuracy, 2), round(stats.accuracy, 2)),
        chart_entry("pp", round(old_stats.pp), round(stats.pp)),
    )

    new_achievements: list[Achievement] = []
    if score.passed and beatmap.has_leaderboard and not user.privileges.is_restricted:
        new_achievements = await app.usecases.score.unlock_achievements(
            score,
            stats,
        )

        # fire amplitude events for each
        for achievement in new_achievements:
            if config.AMPLITUDE_API_KEY:
                job_scheduling.schedule_job(
                    amplitude.track(
                        event_name="achievement_unlocked",
                        user_id=str(score.user_id),
                        device_id=device_id,
                        event_properties={
                            "achievement": amplitude.format_achievement(achievement),
                            "score": amplitude.format_score(score),
                        },
                        time=int(time.time() * 1000),
                    ),
                )

    achievements_str = "/".join(ach.full_name for ach in new_achievements)

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

    end = time.perf_counter()

    logging.info(
        "Processed score submission",
        extra={
            "username": user.name,
            "user_id": user.id,
            "score_id": score.id,
            "beatmap_id": beatmap.id,
            "beatmap_name": beatmap.song_name,
            "game_mode": score.mode.name,
            "performance": score.pp,
            "time_elapsed": end - start,
        },
    )

    return "|".join(submission_charts).encode()
