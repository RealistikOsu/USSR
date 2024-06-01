from __future__ import annotations

from urllib.parse import quote

import aiohttp
import aioredis
import databases
import meilisearch_python_async

import settings
from .storage import AbstractStorage
from .storage import LocalStorage
from .storage import S3Storage

redis: aioredis.Redis = aioredis.from_url(
    f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
)

url = databases.DatabaseURL(
    "mysql+asyncmy://{username}:{password}@{host}:{port}/{db}".format(
        username=settings.MYSQL_USER,
        password=quote(settings.MYSQL_PASSWORD),
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        db=settings.MYSQL_DATABASE,
    ),
)
database: databases.Database = databases.Database(url)
meili = meilisearch_python_async.Client(
    url=settings.MEILI_URL,
    api_key=settings.MEILI_KEY,
)
replay_storage: AbstractStorage

if settings.S3_ENABLED:
    replay_storage = S3Storage(
        settings.S3_REGION,
        settings.S3_ENDPOINT,
        settings.S3_ACCESS_KEY,
        settings.S3_SECRET_KEY,
        settings.S3_BUCKET,
        retries=10,
        timeout=5,
    )
else:
    replay_storage = LocalStorage(settings.DATA_REPLAY_DIRECTORY)

http: aiohttp.ClientSession
