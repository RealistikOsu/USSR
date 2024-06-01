from __future__ import annotations

import app.state
from fastapi.responses import ORJSONResponse


async def get_seasonals():
    db_seasonals = await app.state.services.database.fetch_all(
        "SELECT url FROM seasonal_bg WHERE enabled = 1",
    )

    return ORJSONResponse([seasonal["url"] for seasonal in db_seasonals])
