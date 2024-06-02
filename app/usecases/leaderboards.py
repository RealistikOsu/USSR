from __future__ import annotations

from dataclasses import dataclass

from app.constants.mode import Mode
from app.constants.mods import Mods
from app.models.beatmap import Beatmap
from app.repositories import leaderboards as leaderboards_repository
from app.repositories.leaderboards import LeaderboardScore


@dataclass
class Leaderboard:
    beatmap_md5: str
    mode: Mode
    score_count: int
    scores: list[LeaderboardScore]
    personal_best: LeaderboardScore | None


async def fetch_beatmap_leaderboard(
    beatmap: Beatmap,
    mode: Mode,
    *,
    requestee_user_id: int,
    vanilla_pp_leaderboards: bool,
    mods_filter: Mods | None = None,
    country_filter: str | None = None,
    user_ids_filter: list[int] | None = None,
    leaderboard_size: int = 100,
) -> Leaderboard:
    # if there is a mods filter we will allow non-bests
    # so that a user's best modded score will appear
    best_scores_only = mods_filter is None

    int_mods_filter = int(mods_filter) if mods_filter else None

    sort_column = mode.sort if not vanilla_pp_leaderboards else "pp"

    scores = await leaderboards_repository.fetch_beatmap_leaderboard(
        beatmap_md5=beatmap.md5,
        play_mode=mode.as_vn,
        requestee_user_id=requestee_user_id,
        scores_table=mode.scores_table,
        sort_column=sort_column,
        best_scores_only=best_scores_only,
        mods_filter=int_mods_filter,
        country_filter=country_filter,
        user_ids_filter=user_ids_filter,
        score_limit=leaderboard_size,
    )

    personal_best = await leaderboards_repository.fetch_user_score(
        beatmap_md5=beatmap.md5,
        play_mode=mode.as_vn,
        user_id=requestee_user_id,
        scores_table=mode.scores_table,
        mods_filter=int_mods_filter,
        best_scores_only=best_scores_only,
        sort_column=sort_column,
    )

    score_count = await leaderboards_repository.fetch_beatmap_leaderboard_score_count(
        beatmap_md5=beatmap.md5,
        play_mode=mode.as_vn,
        requestee_user_id=requestee_user_id,
        scores_table=mode.scores_table,
        sort_column=sort_column,
        best_scores_only=best_scores_only,
        mods_filter=int_mods_filter,
        country_filter=country_filter,
        user_ids_filter=user_ids_filter,
    )

    return Leaderboard(
        beatmap_md5=beatmap.md5,
        mode=mode,
        score_count=score_count,
        scores=scores,
        personal_best=personal_best,
    )


async def find_score_rank(
    score_id: int,
    *,
    beatmap_md5: str,
    user_id: int,
    mode: Mode,
) -> int:
    leaderboard_score = await leaderboards_repository.fetch_score_on_leaderboard(
        score_id=score_id,
        beatmap_md5=beatmap_md5,
        play_mode=mode.as_vn,
        user_id=user_id,
        scores_table=mode.scores_table,
        # we always want to use `mode.sort` for score rank since the "real" leaderboards are still score, even if `vanilla_pp_leaderboards`
        sort_column=mode.sort,
    )
    assert leaderboard_score is not None

    return leaderboard_score["score_rank"]
