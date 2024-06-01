from __future__ import annotations

import logging
import time
from urllib.parse import unquote_plus

from fastapi import Depends
from fastapi import Query

import app.state
import app.usecases
from app.constants.leaderboard_type import LeaderboardType
from app.constants.mode import Mode
from app.constants.mods import Mods
from app.models.user import User
from app.repositories.leaderboards import LeaderboardScore
from app.usecases.user import authenticate_user

CUR_LB_VER = 4


def format_leaderboard_score_string(
    mode: Mode,
    leaderboard_score: LeaderboardScore,
    vanilla_pp_leaderboards: bool,
) -> str:
    if mode > Mode.MANIA or vanilla_pp_leaderboards:
        score = int(leaderboard_score["pp"])
    else:
        score = leaderboard_score["score"]

    return (
        f"{leaderboard_score['score_id']}|{leaderboard_score['score_username']}|{score}|{leaderboard_score['max_combo']}|"
        f"{leaderboard_score['count_50']}|{leaderboard_score['count_100']}|{leaderboard_score['count_300']}|{leaderboard_score['count_miss']}|"
        f"{leaderboard_score['count_katu']}|{leaderboard_score['count_geki']}|{int(leaderboard_score['full_combo'])}|"
        f"{leaderboard_score['mods']}|{leaderboard_score['user_id']}|{leaderboard_score['score_rank']}|{leaderboard_score['time']}|"
        "1"  # has replay
    )


async def get_leaderboard(
    user: User = Depends(authenticate_user(Query, "us", "ha")),
    requesting_from_editor_song_select: bool = Query(..., alias="s"),
    leaderboard_version: int = Query(..., alias="vv"),
    leaderboard_type_arg: int = Query(..., alias="v", ge=0, le=4),
    map_md5: str = Query(..., alias="c", min_length=32, max_length=32),
    map_file_name: str = Query(..., alias="f"),
    mode_arg: int = Query(..., alias="m", ge=0, le=3),
    map_set_id: int = Query(..., alias="i", ge=-1, le=2_147_483_647),
    mods_arg: int = Query(..., alias="mods", ge=0, le=2_147_483_647),
    map_package_hash: str = Query(..., alias="h"),  # TODO: whaat to do?
    aqn_files_found: bool = Query(..., alias="a"),  # TODO: whaat to do?
):
    start = time.perf_counter()

    mode = Mode.from_lb(mode_arg, mods_arg)
    mods = Mods(mods_arg)

    if leaderboard_version != CUR_LB_VER:
        await app.usecases.user.restrict_user(
            user,
            "The leaderboard version for the current known latest osu! client is "
            f"{CUR_LB_VER}, but the client sent {leaderboard_version}. (leaderboard gate)",
        )

    beatmap = await app.usecases.beatmap.fetch_by_md5(map_md5)
    if beatmap and beatmap.deserves_update:
        beatmap = await app.usecases.beatmap.update_beatmap(beatmap)

    if not beatmap:
        file_name = unquote_plus(map_file_name)
        map_exists = await app.state.services.database.fetch_val(
            "SELECT 1 FROM beatmaps WHERE file_name = :file_name",
            {"file_name": file_name},
        )
        if map_exists:
            return b"1|false"
        else:
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
        leaderboard_type = LeaderboardType(leaderboard_type_arg)

        mods_filter = mods if leaderboard_type is LeaderboardType.MODS else None
        country_filter = (
            user.country if leaderboard_type is LeaderboardType.COUNTRY else None
        )

        # include their own user id in the filter to ensure the array is never empty
        # this is also just correct because friend lbs should include their own user
        user_ids_filter = (
            user.friends + [user.id]
            if leaderboard_type is LeaderboardType.FRIENDS
            else None
        )

        leaderboard = await app.usecases.leaderboards.fetch_beatmap_leaderboard(
            beatmap,
            mode,
            user.id,
            user.vanilla_pp_leaderboards,
            mods_filter,
            country_filter,
            user_ids_filter,
        )

        response_lines.append(
            beatmap.osu_string(
                score_count=leaderboard.score_count,
                rating=beatmap.rating or 10.0,
            ),
        )

        if leaderboard.personal_best:
            response_lines.append(
                format_leaderboard_score_string(
                    mode,
                    leaderboard.personal_best,
                    user.vanilla_pp_leaderboards,
                ),
            )
        else:
            response_lines.append("")

        response_lines.extend(
            [
                format_leaderboard_score_string(
                    mode,
                    score,
                    user.vanilla_pp_leaderboards,
                )
                for score in leaderboard.scores
            ],
        )

    end = time.perf_counter()

    logging.info(
        "Served leaderboard",
        extra={
            "username": user.name,
            "user_id": user.id,
            "beatmap": beatmap.song_name,
            "mode": mode.name,
            "mods": mods.name,
            "time_elapsed": end - start,
        },
    )

    return "\n".join(response_lines).encode()
