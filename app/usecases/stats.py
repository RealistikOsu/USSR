from __future__ import annotations

from typing import NamedTuple
from typing import Optional

import app.state
import app.usecases
from app.constants.mode import Mode
from app.models.stats import Stats


async def fetch(user_id: int, mode: Mode) -> Optional[Stats]:
    db_stats = await app.state.services.database.fetch_one(
        """
        SELECT ranked_score, total_score, pp, avg_accuracy AS accuracy, playcount,
               playtime, max_combo, total_hits, replays_watched
        FROM user_stats
        WHERE user_id = :user_id
        AND mode = :mode
        """,
        {"user_id": user_id, "mode": mode.value},
    )

    if not db_stats:
        return None

    global_rank, country_rank = await get_redis_rank(user_id, mode)

    return Stats(
        user_id=user_id,
        mode=mode,
        ranked_score=db_stats["ranked_score"],
        total_score=db_stats["total_score"],
        pp=db_stats["pp"],
        rank=global_rank,
        country_rank=country_rank,
        accuracy=db_stats["accuracy"],
        playcount=db_stats["playcount"],
        playtime=db_stats["playtime"],
        max_combo=db_stats["max_combo"],
        total_hits=db_stats["total_hits"],
        replays_watched=db_stats["replays_watched"],
    )


class RankInfo(NamedTuple):
    global_rank: int
    country_rank: int


async def get_redis_rank(user_id: int, mode: Mode) -> RankInfo:
    redis_global_rank = await app.state.services.redis.zrevrank(
        f"ripple:{mode.redis_leaderboard}:{mode.stats_prefix}",
        user_id,
    )
    global_rank = int(redis_global_rank) + 1 if redis_global_rank else 0

    country = await app.usecases.countries.get_country(user_id)
    redis_country_rank = await app.state.services.redis.zrevrank(
        f"ripple:{mode.redis_leaderboard}:{mode.stats_prefix}:{country.lower()}",
        user_id,
    )
    country_rank = int(redis_country_rank) + 1 if redis_country_rank else 0

    return RankInfo(global_rank, country_rank)


async def full_recalc(stats: Stats, score_pp: float) -> None:
    db_scores = await app.state.services.database.fetch_all(
        f"SELECT s.accuracy, s.pp FROM {stats.mode.scores_table} s "
        "JOIN beatmaps b USING(beatmap_md5) "
        "WHERE s.completed = 3 AND s.play_mode = :mode "
        "AND b.ranked IN (3, 2) AND s.userid = :id "
        "ORDER BY s.pp DESC "
        "LIMIT 100",
        {"mode": stats.mode.as_vn, "id": stats.user_id},
    )

    total_acc = 0.0
    total_pp = 0.0
    last_idx = 0

    for idx, score in enumerate(db_scores):
        total_pp += score["pp"] * (0.95**idx)
        total_acc += score["accuracy"] * (0.95**idx)

        last_idx = idx

    stats.accuracy = (total_acc * (100.0 / (20 * (1 - 0.95 ** (last_idx + 1))))) / 100
    stats.pp = total_pp + await calc_bonus(stats)


async def calc_bonus(stats: Stats) -> float:
    count = await app.state.services.database.fetch_val(
        (
            f"SELECT COUNT(*) FROM {stats.mode.scores_table} s "
            "JOIN beatmaps b USING(beatmap_md5) "
            "WHERE b.ranked IN (2, 3) AND s.completed = 3 "
            "AND s.play_mode = :mode AND s.userid = :id "
            "LIMIT 1000"
        ),
        {
            "mode": stats.mode.as_vn,
            "id": stats.user_id,
        },
    )

    return 416.6667 * (1 - (0.995**count))


async def save(stats: Stats) -> None:
    await app.state.services.database.execute(
        (
            """
            UPDATE user_stats
            SET ranked_score = :ranked_score,
                total_score = :total_score,
                pp = :pp,
                avg_accuracy = :avg_accuracy,
                playcount = :playcount,
                playtime = :playtime,
                max_combo = :max_combo,
                total_hits = :total_hits,
                replays_watched = :replays_watched
            WHERE user_id = :user_id
            AND mode = :mode
            """
        ),
        {
            "ranked_score": stats.ranked_score,
            "total_score": stats.total_score,
            "pp": stats.pp,
            "avg_accuracy": stats.accuracy,
            "playcount": stats.playcount,
            "playtime": stats.playtime,
            "max_combo": stats.max_combo,
            "total_hits": stats.total_hits,
            "replays_watched": stats.replays_watched,
            "user_id": stats.user_id,
            "mode": stats.mode.value,
        },
    )


async def update_rank(stats: Stats) -> None:
    mode = stats.mode

    await app.state.services.redis.zadd(
        f"ripple:{mode.redis_leaderboard}:{mode.stats_prefix}",
        {str(stats.user_id): stats.pp},
    )

    country = await app.usecases.countries.get_country(stats.user_id)
    await app.state.services.redis.zadd(
        f"ripple:{mode.redis_leaderboard}:{mode.stats_prefix}:{country.lower()}",
        {str(stats.user_id): stats.pp},
    )

    stats.rank, stats.country_rank = await get_redis_rank(stats.user_id, mode)


async def refresh_stats(user_id: int) -> None:
    await app.state.services.redis.publish("peppy:update_cached_stats", user_id)
