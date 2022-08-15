from __future__ import annotations

import json
from datetime import timedelta
from typing import Optional

import app.state
from app.constants.mode import Mode
from app.models.beatmap import Beatmap
from app.models.score import Score
from app.objects.leaderboard import Leaderboard
from app.objects.redis_lock import RedisLock


async def create(beatmap: Beatmap, mode: Mode) -> Leaderboard:
    leaderboard = Leaderboard(mode)

    db_scores = await app.state.services.database.fetch_all(
        f"SELECT * FROM {mode.scores_table} WHERE beatmap_md5 = :md5 AND play_mode = :mode AND completed = 3",
        {
            "md5": beatmap.md5,
            "mode": mode.as_vn,
        },
    )

    for db_score in db_scores:
        score = Score.from_dict(db_score)
        leaderboard.scores.append(score)

    leaderboard.sort()
    await insert(beatmap, leaderboard)
    return leaderboard


# We expect to handle locking on a per-case basis.
async def fetch(beatmap: Beatmap, mode: Mode) -> Leaderboard:
    if leaderboard := await fetch_cache(beatmap, mode):
        return leaderboard

    leaderboard = await create(beatmap, mode)

    return leaderboard


async def fetch_cache(beatmap: Beatmap, mode: Mode) -> Optional[Leaderboard]:
    redis_cache = await app.state.services.redis.get(
        f"ussr:leaderboards:{beatmap.md5}:{mode.value}",
    )

    if not redis_cache:
        return None

    await app.state.services.redis.expire(
        f"ussr:leaderboards:{beatmap.md5}:{mode.value}",
        timedelta(days=1),
    )

    score_dicts = json.loads(redis_cache)

    return Leaderboard(
        mode=mode,
        scores=[Score.from_dict(score_dict) for score_dict in score_dicts],
    )


# Assumes the lock has already been acquired.
async def insert(beatmap: Beatmap, leaderboard: Leaderboard) -> None:
    serialised_scores = json.dumps(leaderboard.scores_list())
    await app.state.services.redis.set(
        f"ussr:leaderboards:{beatmap.md5}:{leaderboard.mode.value}",
        serialised_scores,
        timedelta(days=1),
    )
