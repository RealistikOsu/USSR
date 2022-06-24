from __future__ import annotations
from typing import Any, Mapping, Optional

import aiohttp
import aioredis
import aiobotocore.client
import databases
from typing import Protocol
from config import config


redis: aioredis.Redis = aioredis.from_url("redis://localhost")

url = databases.DatabaseURL(
    "mysql+asyncmy://{username}:{password}@{host}:3306/{db}".format(
        username=config.DB_USER,
        password=config.DB_PASS,
        host=config.DB_HOST,
        db=config.DB_NAME,
    ),
)
database: databases.Database = databases.Database(url)

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
