# The USSR pubsub router.
from aioredis import Channel
from globals.connections import redis
from typing import Callable
import asyncio

async def wait_for_pub(ch: Channel, h: Callable) -> None:
    """A permanently looping task waiting for the call of a `publish` redis
    event, calling its respective handler upon recevial. Meant to be ran as
    a task.
    
    Args:
        ch (Channel): The publish channel to listen and read from.
        h (Callable): The async
    """

    async for msg in ch.iter(): await h(msg)

async def pubsub_executor(name: str, h: Callable) -> None:
    """Creates an loop task listening to a redis channel with the name `name`
    upon creating it, listening to `publish` events. Upon receival, calls `h`.
    """

    ch, = await redis.subscribe(name)
    asyncio.get_running_loop().create_task(wait_for_pub(ch, h))
