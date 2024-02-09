from __future__ import annotations

import asyncio
from typing import Awaitable
from typing import Callable
from typing import TypedDict

import aioredis.client
import orjson

import app.state
import app.usecases
import logger
from app.constants.mode import Mode
from app.constants.ranked_status import RankedStatus

PUBSUB_HANDLER = Callable[[str], Awaitable[None]]


def register_pubsub(channel: str):
    def decorator(handler: PUBSUB_HANDLER):
        app.state.PUBSUBS[channel] = handler

    return decorator


class UsernameChange(TypedDict):
    userID: str


@register_pubsub("ussr:refresh_bmap")
async def handle_beatmap_status_change(payload: str) -> None:
    """Pubsub to handle beatmap status changes

    This pubsub should be called when a beatmap's status updates
    so that the cache can accordingly refresh.

    It should be published with the payload being the beatmap's md5.
    """

    cached_beatmap = app.usecases.beatmap.md5_from_cache(payload)
    if not cached_beatmap:
        return

    new_beatmap = await app.usecases.beatmap.md5_from_database(payload)
    if new_beatmap is None:
        return

    if new_beatmap.status != cached_beatmap.status:
        # map's status changed, reflect it
        cached_beatmap.status = new_beatmap.status

        # reflect changes in the cache
        app.usecases.beatmap.MD5_CACHE[cached_beatmap.md5] = cached_beatmap
        app.usecases.beatmap.ID_CACHE[cached_beatmap.id] = cached_beatmap
        app.usecases.beatmap.add_to_set_cache(cached_beatmap)

    logger.info(f"Updated {cached_beatmap.song_name} in cache!")

@register_pubsub("ussr:recalculate_user")
async def handle_user_recalculate(payload: str) -> None:
    user_id = int(payload)

    for mode in Mode:
        stats = await app.usecases.stats.fetch(user_id, mode)
        if stats is None:
            logger.warning(
                f"Attempted to recalculate stats for user {user_id} but they don't exist!",
            )
            return
        await app.usecases.stats.full_recalc(stats)
        await app.usecases.stats.update_rank(stats)
        await app.usecases.stats.save(stats)

    logger.info(f"Recalculated user ID {user_id}")


@register_pubsub("ussr:recalculate_user_full")
async def handle_user_recalculate_full(payload: str) -> None:
    user_id = int(payload)

    for mode in Mode:
        stats = await app.usecases.stats.fetch(user_id, mode)
        if stats is None:
            logger.warning(
                f"Attempted to recalculate stats for user {user_id} but they don't exist!",
            )
            return
        await app.usecases.stats.full_recalc(stats)
        await app.usecases.stats.update_rank(stats)
        await app.usecases.stats.calc_playcount(stats)
        await app.usecases.stats.calc_max_combo(stats)
        await app.usecases.stats.calc_total_score(stats)
        await app.usecases.stats.calc_ranked_score(stats)
        await app.usecases.stats.save(stats)

    logger.info(f"Recalculated user ID {user_id}")


class RedisMessage(TypedDict):
    channel: bytes
    data: bytes


async def loop_pubsubs(pubsub: aioredis.client.PubSub) -> None:
    while True:
        try:
            message: RedisMessage = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )
            if message is not None:
                if handler := app.state.PUBSUBS.get(message["channel"].decode()):
                    await handler(message["data"].decode())

            await asyncio.sleep(0.01)
        except asyncio.TimeoutError:
            pass


async def initialise_pubsubs() -> None:
    pubsub = app.state.services.redis.pubsub()
    await pubsub.subscribe(*[channel for channel in app.state.PUBSUBS.keys()])

    pubsub_loop = asyncio.create_task(loop_pubsubs(pubsub))
    app.state.tasks.add(pubsub_loop)
