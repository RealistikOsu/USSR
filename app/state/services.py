from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

import aio_pika
import databases
import httpx
import redis.asyncio as aioredis
from sqlalchemy.sql import ClauseElement

import config

if TYPE_CHECKING:
    from types_aiobotocore_s3.client import S3Client


redis: aioredis.Redis

http_client: httpx.AsyncClient

amqp: aio_pika.abc.AbstractConnection | None
amqp_channel: aio_pika.abc.AbstractChannel | None

s3_client: S3Client | None


class Database:
    def __init__(self, read_dsn: str, write_dsn: str) -> None:
        self.read_database = databases.Database(read_dsn)
        self.write_database = databases.Database(write_dsn)

    async def connect(self) -> None:
        await self.read_database.connect()
        await self.write_database.connect()

    async def disconnect(self) -> None:
        await self.read_database.disconnect()
        await self.write_database.disconnect()

    async def fetch_all(
        self,
        query: ClauseElement | str,
        values: dict[Any, Any] | None = None,
    ) -> list[dict[str, Any]]:
        rows = await self.read_database.fetch_all(query, values)
        return [dict(row._mapping) for row in rows]

    async def fetch_one(
        self,
        query: ClauseElement | str,
        values: dict[Any, Any] | None = None,
    ) -> dict[str, Any] | None:
        row = await self.read_database.fetch_one(query, values)
        if row is None:
            return None

        return dict(row._mapping)

    async def fetch_val(
        self,
        query: ClauseElement | str,
        values: dict[Any, Any] | None = None,
        column: Any = 0,
    ) -> Any:
        val = await self.read_database.fetch_val(query, values, column)
        return val

    async def execute(
        self,
        query: ClauseElement | str,
        values: dict[Any, Any] | None = None,
    ) -> Any:
        result = await self.write_database.execute(query, values)
        return result

    async def execute_many(
        self,
        query: ClauseElement | str,
        values: list[Any],
    ) -> None:
        await self.write_database.execute_many(query, values)


database = Database(
    read_dsn="mysql+asyncmy://{username}:{password}@{host}:{port}/{db}".format(
        username=config.READ_DB_USER,
        password=config.READ_DB_PASS,
        host=config.READ_DB_HOST,
        port=config.READ_DB_PORT,
        db=config.READ_DB_NAME,
    ),
    write_dsn="mysql+asyncmy://{username}:{password}@{host}:{port}/{db}".format(
        username=config.WRITE_DB_USER,
        password=config.WRITE_DB_PASS,
        host=config.WRITE_DB_HOST,
        port=config.WRITE_DB_PORT,
        db=config.WRITE_DB_NAME,
    ),
)
