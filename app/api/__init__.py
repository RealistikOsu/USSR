from __future__ import annotations

from fastapi import APIRouter
from fastapi import Response

router = APIRouter(default_response_class=Response)
