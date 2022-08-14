from __future__ import annotations

import app.state
from app.constants.mode import Mode
from app.models.beatmap import Beatmap
from app.models.score import Score
from app.objects.leaderboard import Leaderboard


async def create(beatmap: Beatmap, mode: Mode) -> Leaderboard:
    leaderboard = Leaderboard(mode)

    db_scores = await app.state.services.read_database.fetch_all(
        f"SELECT * FROM {mode.scores_table} WHERE beatmap_md5 = :md5 AND play_mode = :mode AND completed = 3",
        {
            "md5": beatmap.md5,
            "mode": mode.as_vn,
        },
    )

    for db_score in db_scores:
        score = Score.from_mapping(db_score)
        leaderboard.scores.append(score)

    leaderboard.sort()
    return leaderboard


async def fetch(beatmap: Beatmap, mode: Mode) -> Leaderboard:
    if leaderboard := beatmap.leaderboards.get(mode):
        return leaderboard

    leaderboard = await create(beatmap, mode)
    beatmap.leaderboards[mode] = leaderboard

    return leaderboard
