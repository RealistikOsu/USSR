from __future__ import annotations

import app.state
from app.models.achievement import Achievement

UNSUBMITTED: set[str] = set()
REQUIRES_UPDATE: set[str] = set()
ACHIEVEMENTS: list[Achievement] = []


async def init_cache() -> None:
    db_achievements = await app.state.services.database.fetch_all(
        "SELECT * FROM ussr_achievements",
    )

    for achievement in db_achievements:
        condition = eval(f"lambda score, mode_vn, stats: {achievement['cond']}")
        ACHIEVEMENTS.append(
            Achievement(
                id=achievement["id"],
                file=achievement["file"],
                name=achievement["name"],
                desc=achievement["desc"],
                cond=condition,
            ),
        )
