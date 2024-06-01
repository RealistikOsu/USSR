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

redis: aioredis.Redis = aioredis.from_url("redis://localhost")

url = databases.DatabaseURL(
    "mysql+asyncmy://{username}:{password}@{host}:3306/{db}".format(
        username=config.sql_user,
        password=quote(config.sql_pass),
        host=config.sql_host,
        db=config.sql_db,
    ),
)
database: databases.Database = databases.Database(url)
meili = meilisearch_python_async.Client(
    url=config.meili_url,
    api_key=config.meili_key,
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
