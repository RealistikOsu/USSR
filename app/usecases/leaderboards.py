from __future__ import annotations

import orjson
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
    redis_lb = await app.state.services.redis.sort(
        f"ussr:leaderboards:{beatmap.md5}:{mode.value}:indicies",
        by=f"*->pp" if mode.relax_int else f"*->score",
        get="*->data",
    )

    return Leaderboard(
        mode=mode,
        scores=[Score.from_dict(orjson.loads(score_dict)) for score_dict in redis_lb],
    )


# Assumes the lock has already been acquired.
async def insert(beatmap: Beatmap, leaderboard: Leaderboard) -> None:
    for score_dict in leaderboard.scores_list():
        db_key = f"ussr:leaderboards:{beatmap.md5}:{leaderboard.mode.value}:{score_dict['userid']}"
        await app.state.services.redis.hset(
            name=db_key,
            key="score",
            value=score_dict["pp"] if leaderboard.mode.relax_int else score_dict["score"],
            mapping={ # type: ignore
                "score": score_dict["score"],
                "pp": score_dict["pp"],
                "data": score_dict,
            },
        )

        await app.state.services.redis.sadd(
            f"ussr:leaderboards:{beatmap.md5}:{leaderboard.mode.value}:indicies",
            db_key,
        )
