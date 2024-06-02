from __future__ import annotations

import asyncio
from types import TracebackType
from typing import Optional

import app.state.services

DEFAULT_LOCK_EXPIRY = 10  # in seconds
DEFAULT_RETRY_DELAY = 0.05  # in seconds


class RedisLock:
    def __init__(self, key: str) -> None:
        self.key = key

    async def _try_acquire(self, expiry: int) -> bool:
        val = await app.state.services.redis.set(self.key, "1", ex=expiry, nx=True)
        return bool(val)

    async def acquire(
        self,
        expiry: int = DEFAULT_LOCK_EXPIRY,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ) -> None:
        while not await self._try_acquire(expiry):
            await asyncio.sleep(retry_delay)

    async def release(self) -> None:
        await app.state.services.redis.delete(self.key)

    async def __aenter__(self) -> None:
        await self.acquire()

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.release()
