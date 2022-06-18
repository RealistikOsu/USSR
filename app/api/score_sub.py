from __future__ import annotations

import hashlib
import os
import time
from base64 import b64decode
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
import logger
from app.constants.score_status import ScoreStatus
from app.models.score import Score
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


MAPS_PATH = f"{config.DATA_DIR}/maps"


async def check_local_file(osu_file_path: str, map_id: int, map_md5: str) -> bool:
    with open(osu_file_path, "rb") as f:
        if not osu_file_path.exists() or hashlib.md5(f.read()).hexdigest() != map_md5:
            async with app.state.services.http.get(
                f"https://old.ppy.sh/osu/{map_id}",
            ) as response:
                if response.status != 200:
                    return False

                osu_file = await response.read()

    with open(osu_file_path, "wb") as f:
        f.write(osu_file)

    return True


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

    beatmap_md5 = score_data[0]
    if not (beatmap := await app.usecases.beatmap.fetch_by_md5(beatmap_md5)):
        return b"error: beatmap"

    username = score_data[1].rstrip()
    if not (user := await app.usecases.user.auth_user(username, password_md5)):
        return  # empty resp tells osu to retry

    score = Score.from_submission(score_data[2:], beatmap_md5, user)
    leaderboard = await app.usecases.leaderboards.fetch(beatmap, score.mode)

    score.acc = app.usecases.score.calculate_accuracy(score)
    score.quit = exited_out

    if not score.mods.rankable:
        return b"error: no"

    if not token and not config.CUSTOM_CLIENTS:
        await app.usecases.user.restrict_user(user, "Tampering with osu!auth.")

    if user_agent != "osu!":
        await app.usecases.user.restrict_user(user, "Score submitter.")

    if score.mods.conflict:
        await app.usecases.user.restrict_user(
            user,
            "Illegal mod combo (score submitter).",
        )

    osu_file_path = os.path.join(MAPS_PATH, f"{beatmap.id}.osu")
    if await check_local_file(osu_file_path, beatmap.id, beatmap.md5):
        if beatmap.mode.as_vn == score.mode.as_vn:
            # only get pp if the map is not a convert
            # convert support will come later
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
