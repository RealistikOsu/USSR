from __future__ import annotations

from typing import Any
from typing import Mapping
from typing import Optional
from typing import Protocol

import aio_pika
import aiohttp
import aioredis
import databases
from ftpretty import ftpretty
from sqlalchemy.sql import ClauseElement

import config


redis: aioredis.Redis = aioredis.from_url("redis://localhost")

ftp_client: ftpretty

http: aiohttp.ClientSession

amqp: aio_pika.RobustConnection
amqp_channel: aio_pika.RobustChannel


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
        values: dict | None = None,
    ) -> list[Mapping]:
        rows = await self.read_database.fetch_all(query, values)  # type: ignore
        return [row._mapping for row in rows]

    async def fetch_one(
        self,
        query: ClauseElement | str,
        values: dict | None = None,
    ) -> Mapping | None:
        row = await self.read_database.fetch_one(query, values)  # type: ignore
        if row is None:
            return None

        return row._mapping

    async def fetch_val(
        self,
        query: ClauseElement | str,
        values: dict | None = None,
        column: Any = 0,
    ) -> Any:
        val = await self.read_database.fetch_val(query, values, column)  # type: ignore
        return val

    async def execute(
        self,
        query: ClauseElement | str,
        values: dict | None = None,
    ) -> Any:
        result = await self.write_database.execute(query, values)  # type: ignore
        return result

    async def execute_many(
        self,
        query: ClauseElement | str,
        values: list,
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


class S3Client(Protocol):
    # TODO: could do the types correctly? lol
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.put_object
    async def put_object(self, Bucket: str, Key: str, Body: bytes):
        ...

    async def generate_presigned_url(
        self,
        ClientMethod: str,
        Params: Optional[Mapping[str, Any]] = None,
        ExpiresIn: int = 3600,
        HttpMethod: Optional[str] = None,  # TODO: literal?
    ) -> str:
        ...

    async def close(self) -> None:
        ...


s3_client: S3Client
