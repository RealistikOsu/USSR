from __future__ import annotations

import logging
import time
from urllib.parse import unquote_plus

from fastapi import Depends
from fastapi import Query

import app.state
import app.usecases
import app.utils
from app.constants.leaderboard_type import LeaderboardType
from app.constants.mode import Mode
from app.constants.mods import Mods
from app.models.score import Score
from app.models.user import User
from app.usecases.user import authenticate_user

CUR_LB_VER = 4


async def get_leaderboard(
    user: User = Depends(authenticate_user(Query, "us", "ha")),
    requesting_from_editor_song_select: bool = Query(..., alias="s"),
    leaderboard_version: int = Query(..., alias="vv"),
    leaderboard_type_arg: int = Query(..., alias="v", ge=0, le=4),
    map_md5: str = Query(..., alias="c", min_length=32, max_length=32),
    map_filename: str = Query(..., alias="f"),
    mode_arg: int = Query(..., alias="m", ge=0, le=3),
    map_set_id: int = Query(..., alias="i", ge=-1, le=2_147_483_647),
    mods_arg: int = Query(..., alias="mods", ge=0, le=2_147_483_647),
    map_package_hash: str = Query(..., alias="h"),  # TODO: whaat to do?
    aqn_files_found: bool = Query(..., alias="a"),  # TODO: whaat to do?
):
    start = time.perf_counter_ns()

    if map_md5 in app.state.cache.UNSUBMITTED:
        return b"-1|false"
    elif map_md5 in app.state.cache.REQUIRES_UPDATE:
        return b"1|false"

    mode = Mode.from_lb(mode_arg, mods_arg)
    mods = Mods(mods_arg)

    if leaderboard_version != CUR_LB_VER:
        await app.usecases.user.restrict_user(
            user,
            "The leaderboard version for the current known latest osu! client is "
            f"{CUR_LB_VER}, but the client sent {leaderboard_version}. (leaderboard gate)",
        )

    has_set_id = map_set_id > 0
    if has_set_id:
        await app.usecases.beatmap.fetch_by_set_id(map_set_id)

    beatmap = await app.usecases.beatmap.fetch_by_md5(map_md5)
    if beatmap and beatmap.deserves_update:
        beatmap = await app.usecases.beatmap.update_beatmap(beatmap)

    if not beatmap:
        if has_set_id and map_set_id not in app.usecases.beatmap.SET_CACHE:
            app.state.cache.UNSUBMITTED.add(map_md5)
            return b"-1|false"

        filename = unquote_plus(map_filename)
        if has_set_id:
            for bmap in app.usecases.beatmap.SET_CACHE[map_set_id]:
                if bmap.filename == filename:
                    map_exists = True
                    break
            else:
                map_exists = False
        else:
            map_exists = await app.state.services.database.fetch_val(
                "SELECT 1 FROM beatmaps WHERE file_name = :filename",
                {"filename": filename},
            )

        if map_exists:
            app.state.cache.REQUIRES_UPDATE.add(map_md5)
            return b"1|false"
        else:
            if map_md5 not in app.state.cache.UNSUBMITTED:
                app.state.cache.UNSUBMITTED.add(map_md5)

            return b"-1|false"

    if not beatmap.has_leaderboard:
        return f"{beatmap.status.value}|false".encode()

    response_lines: list[str] = []

    if requesting_from_editor_song_select:
        response_lines.append(
            beatmap.osu_string(
                score_count=0,
                rating=beatmap.rating or 10.0,
            ),
        )
    else:
        # real leaderboard, let's get some scores!
        leaderboard = await app.usecases.leaderboards.fetch(beatmap, mode)

        response_lines.append(
            beatmap.osu_string(
                score_count=len(leaderboard),
                rating=beatmap.rating or 10.0,
            ),
        )

        personal_best = await leaderboard.find_user_score(user.id)
        if personal_best:
            response_lines.append(
                personal_best["score"].osu_string(
                    user.name,
                    personal_best["rank"],
                ),
            )
        else:
            response_lines.append("")

        leaderboard_type = LeaderboardType(leaderboard_type_arg)

        scores: list[Score] = []

        mod_arg = None
        if leaderboard_type == LeaderboardType.MODS:
            mod_arg = mods

        for score in await leaderboard.get_unrestricted_scores(user.id, mods=mod_arg):
            if len(scores) >= 100:  # max 100 scores on lb
                break

            if leaderboard_type == LeaderboardType.MODS and score.mods != mods:
                continue

            score_country = await app.usecases.countries.get_country(score.user_id)
            if (
                leaderboard_type == LeaderboardType.COUNTRY
                and score_country != user.country
            ):
                continue

            if (
                leaderboard_type == LeaderboardType.FRIENDS
                and score.user_id not in user.friends
            ):
                continue

            scores.append(score)

        # this double loop probably seems pointless
        # however it's necessary to be able to limit score count and get accurate ranking at the same time
        for idx, score in enumerate(scores):
            if score.user_id == user.id:
                displayed_name = user.name
            else:
                score_clan = await app.usecases.clans.get_clan(score.user_id)
                score_username = await app.usecases.usernames.get_username(
                    score.user_id,
                )

                if score_clan:
                    displayed_name = f"[{score_clan}] {score_username}"
                else:
                    displayed_name = score_username

            response_lines.append(score.osu_string(displayed_name, rank=idx + 1))

    end = time.perf_counter_ns()

    logging.info(
        "Served leaderboard",
        extra={
            "username": user.name,
            "user_id": user.id,
            "beatmap": beatmap.song_name,
            "mode": mode.name,
            "mods": mods.name,
            "time_elapsed": app.utils.format_time(end - start),
        },
    )

    return "\n".join(response_lines).encode()
