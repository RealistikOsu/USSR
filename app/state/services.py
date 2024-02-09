from __future__ import annotations

from urllib.parse import quote

import aiohttp
import aioredis
import databases
import meilisearch_python_async

import app.utils
from config import config
from .storage import AbstractStorage, LocalStorage, S3Storage

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

if config.s3_enabled:
    replay_storage = S3Storage(
        config.s3_region,
        config.s3_endpoint,
        config.s3_access_key,
        config.s3_secret_key,
        config.s3_bucket,
        retries=10,
        timeout=5
    )
else:
    replay_storage = LocalStorage(str(app.utils.REPLAYS))

http: aiohttp.ClientSession
