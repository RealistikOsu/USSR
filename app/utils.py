from __future__ import annotations

import os
import logging
from typing import Optional
from typing import Union

from aiohttp import ClientSession

import app.state
from app.objects.path import Path
import config

REQUIRED_FOLDERS = (
    config.DATA_DIR,
    f"{config.DATA_DIR}/beatmaps",
    f"{config.DATA_DIR}/screenshots",
)

DATA_PATH = Path(config.DATA_DIR)


def ensure_directory_structure() -> None:
    for folder in REQUIRED_FOLDERS:
        if not os.path.exists(folder):
            logging.warning(f"Creating data folder {folder}...")
            os.makedirs(folder, exist_ok=True)


def make_safe(username: str) -> str:
    return username.rstrip().lower().replace(" ", "_")


TIME_ORDER_SUFFIXES = ["ns", "μs", "ms", "s"]


def format_time(time: Union[int, float]) -> str:
    for suffix in TIME_ORDER_SUFFIXES:
        if time < 1000:
            break

        time /= 1000

    return f"{time:.2f}{suffix}"  # type: ignore


async def channel_message(channel: str, message: str) -> None:
    async with ClientSession() as sesh:
        await sesh.get(
            "http://localhost:5001/api/v1/fokabotMessage",
            params={
                "to": channel,
                "msg": message,
                "k": config.FOKABOT_KEY,
            },
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
