from __future__ import annotations

from fastapi import APIRouter
from fastapi import Response

from . import leaderboards

router = APIRouter(default_response_class=Response)

router.add_api_route("/web/osu-osz2-getscores.php", leaderboards.get_leaderboard)
