from __future__ import annotations

import asyncio
from typing import Awaitable
from typing import Callable
from typing import Optional
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


@register_pubsub("peppy:ban")
async def handle_privilege_change(payload: str) -> None:
    user_id = int(payload)
    await app.usecases.privileges.update_privilege(user_id)

    logger.info(f"Updated privileges for user ID {user_id}")


@register_pubsub("peppy:wipe")
async def handle_player_wipe(payload: str) -> None:
    user_id, rx_int, mode_int = [int(part) for part in payload.split(",")]
    mods_int = {
        0: 0,  # vn = nomod
        1: 128,  # rx = relax
        2: 8192,  # ap = autopilot
    }[rx_int]

    mode = Mode.from_lb(mode_int, mods_int)
    beatmaps = await app.usecases.beatmap.fetch_all_cache()

    for beatmap in beatmaps:
        if not (leaderboard := beatmap.leaderboards.get(mode)):
            continue

        await leaderboard.remove_user(user_id)

    logger.info(f"Handled wipe for user ID {user_id} on {mode!r}")


class UsernameChange(TypedDict):
    userID: str


@register_pubsub("peppy:change_username")
async def handle_username_change(payload: str) -> None:
    data: UsernameChange = orjson.loads(payload)
    user_id = int(data["userID"])

    username = await app.usecases.usernames.update_username(user_id)
    logger.info(f"Updated user ID {user_id}'s username to {username}")


@register_pubsub("cache:map_update")
async def handle_beatmap_status_change(payload: str) -> None:
    """Pubsub to handle beatmap status changes

    This pubsub should be called when a beatmap's status updates
    so that the cache can accordingly refresh.

    It should be published with the payload being the beatmap's md5 and new status
    """
    beatmap_md5, _ = payload.split(",", maxsplit=1)

    cached_beatmap = app.usecases.beatmap.md5_from_cache(beatmap_md5)
    if not cached_beatmap:
        return

    new_beatmap = await app.usecases.beatmap.md5_from_database(beatmap_md5)

    if new_beatmap is None:
        return

    if new_beatmap.status != cached_beatmap.status:
        # map's status changed, reflect it
        cached_beatmap.status = new_beatmap.status

        if new_beatmap.status not in (
            RankedStatus.RANKED,
            RankedStatus.LOVED,
            RankedStatus.APPROVED,
            RankedStatus.QUALIFIED,
        ):
            # reset the leaderboards if they should no longer show
            cached_beatmap.leaderboards = {}

        # reflect changes in the cache
        app.usecases.beatmap.MD5_CACHE[cached_beatmap.md5] = cached_beatmap
        app.usecases.beatmap.ID_CACHE[cached_beatmap.id] = cached_beatmap
        app.usecases.beatmap.add_to_set_cache(cached_beatmap)

    logger.info(f"Updated {cached_beatmap.song_name} in cache!")


@register_pubsub("api:update_clan")
async def handle_clan_change(payload: str) -> None:
    clan_id = int(payload)

    clan_users = await app.state.services.database.fetch_all(
        "SELECT user FROM user_clans WHERE clan = :id",
        {"id": clan_id},
    )

    for clan_user in clan_users:
        await app.usecases.clans.update_clan(clan_user["user"])

    logger.info(f"Updated tag for clan ID {clan_id}")


class RedisMessage(TypedDict):
    channel: bytes
    data: bytes


async def loop_pubsubs(pubsub: aioredis.client.PubSub) -> None:
    while True:
        try:
            message: Optional[RedisMessage] = await pubsub.get_message(
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
