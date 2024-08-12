from __future__ import annotations

import app.usecases


async def total_scores_set() -> int:
    return await app.usecases.aggregate_score_stats.total_scores_set()
