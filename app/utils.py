from __future__ import annotations

import os
from typing import Optional
from typing import Union
from urllib.parse import urlencode

from aiohttp import ClientSession

import app.state
import logger
from app.objects.path import Path
from config import config

REQUIRED_FOLDERS = (
    config.DATA_DIR,
    f"{config.DATA_DIR}/beatmaps/",
    f"{config.DATA_DIR}/screenshots/",
)

DATA_PATH = Path(config.DATA_DIR)


def ensure_folders():
    for folder in REQUIRED_FOLDERS:
        if not os.path.exists(folder):
            logger.warning(f"Creating data folder {folder}...")
            os.makedirs(folder, exist_ok=True)


def make_safe(username: str) -> str:
    return username.rstrip().lower().replace(" ", "_")


TIME_ORDER_SUFFIXES = ["ns", "μs", "ms", "s"]


def format_time(time: Union[int, float]) -> str:
    for suffix in TIME_ORDER_SUFFIXES:
        if time < 1000:
            break

        time /= 1000

    return f"{time:.2f}{suffix}"


async def channel_message(channel: str, message: str) -> None:
    params = urlencode(
        {
            "to": channel,
            "msg": message,
            "k": config.FOKABOT_KEY,
        },
    )

    async with ClientSession() as sesh:
        await sesh.get(
            f"http://localhost:5001/api/v1/fokabotMessage?{params}",
            timeout=2,
        )


async def announce(message: str) -> None:
    await channel_message("#announce", message)


async def check_online(user_id: int, ip: Optional[str] = None) -> bool:
    key = f"peppy:sessions:{user_id}"

    if ip:
        return await app.state.services.redis.sismember(key, ip)

    return await app.state.services.redis.exists(key)


def ts_to_utc_ticks(ts: int) -> int:
    """Converts a UNIX timestamp to a UTC ticks. Equivalent to the reverse of
    C#'s `DateTime.ToUniversalTime().Ticks`.
    """

    return int(ts * 1e7) + 0x89F7FF5F7B58000
