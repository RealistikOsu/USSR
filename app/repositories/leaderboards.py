from __future__ import annotations

from typing import cast
from typing import Literal
from typing import TypedDict

import app.state


class LeaderboardScore(TypedDict):
    score_id: int
    user_id: int
    score: int
    max_combo: int
    full_combo: bool
    mods: int
    count_300: int
    count_100: int
    count_50: int
    count_geki: int
    count_katu: int
    count_miss: int
    time: int
    play_mode: int
    completed: int
    accuracy: float
    pp: float
    checksum: str | None
    patcher: bool
    pinned: bool
    score_rank: int
    score_username: str


async def fetch_beatmap_leaderboard(
    beatmap_md5: str,
    play_mode: int,
    requestee_user_id: int,
    scores_table: Literal["scores", "scores_relax", "scores_ap"],
    mods_filter: int | None = None,
    country_filter: str | None = None,
    user_ids_filter: list[int] | None = None,
    best_scores_only: bool = True,
    score_limit: int = 100,
    sort_column: Literal["pp", "score"] = "pp",
) -> list[LeaderboardScore]:
    params = {
        "beatmap_md5": beatmap_md5,
        "requestee_user_id": requestee_user_id,
        "play_mode": play_mode,
        "score_limit": score_limit,
    }

    if best_scores_only:
        completed_query_fragment = "= 3"
    else:
        completed_query_fragment = "IN (2, 3)"

    extra_queries = []

    if mods_filter is not None:
        extra_queries.append("s.mods = :mods_filter")
        params["mods_filter"] = mods_filter

    if country_filter is not None:
        extra_queries.append("users_stats.country = :country_filter")
        params["country_filter"] = country_filter

    if user_ids_filter is not None:
        extra_queries.append("s.userid IN :user_ids_filter")
        params["user_ids_filter"] = tuple(user_ids_filter)

    if len(extra_queries) > 0:
        extra_query = "AND " + " AND ".join(extra_queries)
    else:
        extra_query = ""

    query = f"""
        WITH RankedScores AS (
            SELECT
                c.tag,
                users.username AS users_username,
                s.id AS score_id,
                s.beatmap_md5 AS beatmap_md5,
                s.userid AS user_id,
                s.score AS score,
                s.max_combo AS max_combo,
                s.full_combo AS full_combo,
                s.mods AS mods,
                s.`300_count` AS count_300,
                s.`100_count` AS count_100,
                s.`50_count` AS count_50,
                s.katus_count AS count_katu,
                s.gekis_count AS count_geki,
                s.misses_count AS count_miss,
                s.time AS time,
                s.play_mode AS play_mode,
                s.completed AS completed,
                s.accuracy AS accuracy,
                s.pp AS pp,
                s.checksum AS checksum,
                s.patcher AS patcher,
                s.pinned AS pinned,
                row_number() OVER (PARTITION BY s.userid ORDER BY s.{sort_column} DESC) score_order_rank
            FROM {scores_table} s
            INNER JOIN users ON users.id = s.userid
            LEFT JOIN clans c ON users.clan_id = c.id
            INNER JOIN users_stats ON users_stats.id = s.userid
            WHERE
                s.beatmap_md5 = :beatmap_md5
                AND s.play_mode = :play_mode
                AND s.completed {completed_query_fragment}
                AND (users.privileges & 1 > 0 OR users.id = :requestee_user_id)
                {extra_query}
        )
        SELECT
            CONCAT(IF(a.tag IS NOT NULL AND a.user_id != :requestee_user_id, CONCAT("[", a.tag, "] "), ""), a.users_username) `score_username`,
            a.*
        FROM (
            SELECT *, row_number() OVER (ORDER BY {sort_column} DESC) `score_rank`
            FROM RankedScores
            WHERE score_order_rank = 1
        ) a
        ORDER BY a.{sort_column} DESC
        LIMIT :score_limit
    """

    score_records = await app.state.services.database.fetch_all(query, params)
    return cast(
        list[LeaderboardScore],
        [dict(score_record) for score_record in score_records],
    )


async def fetch_user_score(
    beatmap_md5: str,
    play_mode: int,
    user_id: int,
    scores_table: Literal["scores", "scores_relax", "scores_ap"],
    mods_filter: int | None = None,
    best_scores_only: bool = True,
    sort_column: Literal["pp", "score"] = "pp",
) -> LeaderboardScore | None:
    params = {
        "beatmap_md5": beatmap_md5,
        "play_mode": play_mode,
        "user_id": user_id,
    }
    if best_scores_only:
        completed_query_fragment = "= 3"
    else:
        completed_query_fragment = "IN (2, 3)"

    extra_query = ""
    if mods_filter is not None:
        extra_query = " AND mods = :mods_filter "
        params["mods_filter"] = mods_filter

    query = f"""
        WITH RankedScores AS (
            SELECT
                users.username AS users_username,
                s.id AS score_id,
                s.beatmap_md5 AS beatmap_md5,
                s.userid AS user_id,
                s.score AS score,
                s.max_combo AS max_combo,
                s.full_combo AS full_combo,
                s.mods AS mods,
                s.`300_count` AS count_300,
                s.`100_count` AS count_100,
                s.`50_count` AS count_50,
                s.katus_count AS count_katu,
                s.gekis_count AS count_geki,
                s.misses_count AS count_miss,
                s.time AS time,
                s.play_mode AS play_mode,
                s.completed AS completed,
                s.accuracy AS accuracy,
                s.pp AS pp,
                s.checksum AS checksum,
                s.patcher AS patcher,
                s.pinned AS pinned,
                row_number() OVER (PARTITION BY s.userid ORDER BY s.{sort_column} DESC) score_order_rank
            FROM {scores_table} s
            INNER JOIN users ON users.id = s.userid
            WHERE
                s.beatmap_md5 = :beatmap_md5
                AND s.play_mode = :play_mode
                AND s.completed {completed_query_fragment}
                AND (users.privileges & 1 > 0 OR users.id = :user_id)
                {extra_query}
        )
        SELECT
            a.*,
            a.users_username AS score_username
        FROM (
            SELECT *, row_number() OVER (ORDER BY {sort_column} DESC) `score_rank`
            FROM RankedScores
            WHERE score_order_rank = 1
        ) a
        WHERE a.user_id = :user_id
        ORDER BY a.{sort_column} DESC
        LIMIT 1
    """

    score_record = await app.state.services.database.fetch_one(query, params)
    return (
        cast(LeaderboardScore, dict(score_record)) if score_record is not None else None
    )


async def fetch_score_on_leaderboard(
    score_id: int,
    beatmap_md5: str,
    play_mode: int,
    user_id: int,
    scores_table: Literal["scores", "scores_relax", "scores_ap"],
    sort_column: Literal["pp", "score"] = "pp",
) -> LeaderboardScore | None:
    params = {
        "beatmap_md5": beatmap_md5,
        "play_mode": play_mode,
        "user_id": user_id,
        "score_id": score_id,
    }

    query = f"""
        SELECT
            users.username AS users_username,
            s.id AS score_id,
            s.beatmap_md5 AS beatmap_md5,
            s.userid AS user_id,
            s.score AS score,
            s.max_combo AS max_combo,
            s.full_combo AS full_combo,
            s.mods AS mods,
            s.`300_count` AS count_300,
            s.`100_count` AS count_100,
            s.`50_count` AS count_50,
            s.katus_count AS count_katu,
            s.gekis_count AS count_geki,
            s.misses_count AS count_miss,
            s.time AS time,
            s.play_mode AS play_mode,
            s.completed AS completed,
            s.accuracy AS accuracy,
            s.pp AS pp,
            s.checksum AS checksum,
            s.patcher AS patcher,
            s.pinned AS pinned,
            (
                SELECT COUNT(*) + 1
                FROM {scores_table} b
                INNER JOIN users u ON b.userid = u.id
                WHERE
                    b.beatmap_md5 = :beatmap_md5
                    AND b.play_mode = :play_mode
                    AND b.completed = 3
                    AND (u.privileges & 1 > 0 OR u.id = :user_id)
                    AND (
                        b.{sort_column} > s.{sort_column}
                        OR (
                            b.{sort_column} = s.{sort_column}
                            AND b.time > s.time
                        )
                    )
            ) AS score_rank
        FROM {scores_table} s
        INNER JOIN users ON s.userid = users.id
        WHERE s.id = :score_id
    """

    score_record = await app.state.services.database.fetch_one(query, params)
    return (
        cast(LeaderboardScore, dict(score_record)) if score_record is not None else None
    )


async def fetch_beatmap_leaderboard_score_count(
    beatmap_md5: str,
    play_mode: int,
    requestee_user_id: int,
    scores_table: Literal["scores", "scores_relax", "scores_ap"],
    mods_filter: int | None = None,
    country_filter: str | None = None,
    user_ids_filter: list[int] | None = None,
    best_scores_only: bool = True,
    sort_column: Literal["pp", "score"] = "pp",
) -> int:
    params = {
        "beatmap_md5": beatmap_md5,
        "requestee_user_id": requestee_user_id,
        "play_mode": play_mode,
    }

    if best_scores_only:
        completed_query_fragment = "= 3"
    else:
        completed_query_fragment = "IN (2, 3)"

    extra_queries = []

    if mods_filter is not None:
        extra_queries.append("s.mods = :mods_filter")
        params["mods_filter"] = mods_filter

    if country_filter is not None:
        extra_queries.append("users_stats.country = :country_filter")
        params["country_filter"] = country_filter

    if user_ids_filter is not None:
        extra_queries.append("s.userid IN :user_ids_filter")
        params["user_ids_filter"] = tuple(user_ids_filter)

    if len(extra_queries) > 0:
        extra_query = "AND " + " AND ".join(extra_queries)
    else:
        extra_query = ""

    query = f"""
        WITH RankedScores AS (
            SELECT
                users.username AS users_username,
                s.id AS score_id,
                s.beatmap_md5 AS beatmap_md5,
                s.userid AS user_id,
                s.score AS score,
                s.max_combo AS max_combo,
                s.full_combo AS full_combo,
                s.mods AS mods,
                s.`300_count` AS count_300,
                s.`100_count` AS count_100,
                s.`50_count` AS count_50,
                s.katus_count AS count_katu,
                s.gekis_count AS count_geki,
                s.misses_count AS count_miss,
                s.time AS time,
                s.play_mode AS play_mode,
                s.completed AS completed,
                s.accuracy AS accuracy,
                s.pp AS pp,
                s.checksum AS checksum,
                s.patcher AS patcher,
                s.pinned AS pinned,
                row_number() OVER (PARTITION BY s.userid ORDER BY s.{sort_column} DESC) score_order_rank
            FROM {scores_table} s
            INNER JOIN users ON users.id = s.userid
            INNER JOIN users_stats ON users_stats.id = s.userid
            WHERE
                s.beatmap_md5 = :beatmap_md5
                AND s.play_mode = :play_mode
                AND s.completed {completed_query_fragment}
                AND (users.privileges & 1 > 0 OR users.id = :requestee_user_id)
                {extra_query}
        )
        SELECT
            COUNT(*)
        FROM (
            SELECT *, row_number() OVER (ORDER BY {sort_column} DESC) `score_rank`
            FROM RankedScores
            WHERE score_order_rank = 1
        ) a
    """

    score_count = await app.state.services.database.fetch_val(query, params)
    return int(score_count)
