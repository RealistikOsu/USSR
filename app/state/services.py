from __future__ import annotations

from typing import Any
from typing import Mapping
from typing import Optional
from typing import Protocol
from ftpretty import ftpretty

import aiohttp
import aioredis
from app.objects.database import Database

import config


redis: aioredis.Redis = aioredis.from_url("redis://localhost")

ftp_client: ftpretty

database: Database = Database(
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

http: aiohttp.ClientSession


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
