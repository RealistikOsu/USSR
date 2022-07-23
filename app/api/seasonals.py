from __future__ import annotations

from fastapi.responses import ORJSONResponse

import app.state


async def get_seasonals():
    db_seasonals = await app.state.services.read_database.fetch_all(
        "SELECT url FROM seasonal_bg WHERE enabled = 1",
    )

    return ORJSONResponse([seasonal["url"] for seasonal in db_seasonals])
