from __future__ import annotations

import aiohttp
import aioredis
import databases

from config import config

redis: aioredis.Redis = aioredis.from_url("redis://localhost")

url = databases.DatabaseURL(
    "mysql+asyncmy://{username}:{password}@{host}:3306/{db}".format(
        username=config.SQL_USER,
        password=config.SQL_PASS,
        host=config.SQL_HOST,
        db=config.SQL_DB,
    ),
)
database: databases.Database = databases.Database(url)

http: aiohttp.ClientSession
