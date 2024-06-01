from __future__ import annotations

from typing import Optional
from typing import Union

import orjson

import app.state


def make_safe(username: str) -> str:
    return username.rstrip().lower().replace(" ", "_")


_TIME_ORDER_SUFFIXES = ["ns", "μs", "ms", "s"]


def format_time(time: Union[int, float]) -> str:
    for suffix in _TIME_ORDER_SUFFIXES:
        if time < 1000:
            break

        time /= 1000

    return f"{time:.2f}{suffix}" # type: ignore


async def channel_message(channel: str, message: str) -> None:
    msg = orjson.dumps(
        {
            "to": channel,
            "message": message,
        },
    )

    await app.state.services.redis.publish("peppy:bot_msg", msg)


async def announce(message: str) -> None:
    await channel_message("#announce", message)


async def notify_new_score(score_id: int) -> None:
    await app.state.services.redis.publish("api:score_submission", score_id)


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
