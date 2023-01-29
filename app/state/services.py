from __future__ import annotations

from urllib.parse import quote

import aiohttp
import aioredis
import databases
import meilisearch_python_async

from config import config

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

http: aiohttp.ClientSession
