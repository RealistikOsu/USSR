from __future__ import annotations

import time
from typing import Any
from typing import Mapping

from tenacity import retry
from tenacity import stop_after_attempt

import config
from app.state import services


# TODO: better client error & 429 handling
@retry(stop=stop_after_attempt(7))
async def track(
    event_name: str,
    user_id: str | None,
    device_id: str | None,
    event_properties: Mapping[str, Any] | None = None,
    user_properties: Mapping[str, Any] | None = None,
) -> None:
    if event_properties is None:
        event_properties = {}
    if user_properties is None:
        user_properties = {}
    async with services.http.post(
        url="https://api.amplitude.com/2/httpapi",
        headers={"Content-Type": "application/json"},
        json={
            "api_key": config.AMPLITUDE_API_KEY,
            "options": {
                # (akatsuki's user ids start from 1000)
                "min_id_length": 4,
            },
            "events": [
                {
                    "user_id": user_id,
                    "device_id": device_id,
                    "event_type": event_name,
                    "event_properties": event_properties,
                    "user_properties": user_properties,
                    "time": int(time.time() * 1000),
                },
            ],
        },
    ) as resp:
        resp.raise_for_status()


@retry(stop=stop_after_attempt(7))
async def identify(
    user_id: str | None,
    device_id: str | None,
    user_properties: Mapping[str, Any] | None = None,
) -> None:
    async with services.http.post(
        url="https://api.amplitude.com/identify",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "api_key": config.AMPLITUDE_API_KEY,
            "identification": [
                {
                    "user_id": user_id,
                    "device_id": device_id,
                    "user_properties": user_properties,
                },
            ],
        },
    ) as resp:
        resp.raise_for_status()
