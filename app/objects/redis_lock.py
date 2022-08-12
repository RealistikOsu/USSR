# https://github.com/osuAkatsuki/bancho-service/blob/57537f718ed991f5065e37983a04e1432bd510ed/objects/redis_lock.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import TracebackType
from typing import Optional

import aioredis

import app.state


@dataclass
class RedisLock:
    redis: aioredis.Redis
    lock_key: str

    async def acquire(self) -> None:
        locked = int(await self.redis.get(self.lock_key) or 0) == 1
        while locked:
            locked = int(await self.redis.get(self.lock_key)) == 1
            await asyncio.sleep(0.1)

        await self.redis.set(self.lock_key, 1)

    async def release(self) -> None:
        await self.redis.set(self.lock_key, 0)

    async def __aenter__(self) -> RedisLock:
        await self.acquire()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.release()
