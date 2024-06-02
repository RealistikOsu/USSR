from __future__ import annotations

from fastapi import Response
from fastapi.responses import ORJSONResponse

import app.state


async def get_seasonals() -> Response:
    db_seasonals = await app.state.services.database.fetch_all(
        "SELECT url FROM seasonal_bg WHERE enabled = 1",
    )

    return ORJSONResponse([seasonal["url"] for seasonal in db_seasonals])
