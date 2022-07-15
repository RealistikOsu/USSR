from __future__ import annotations

import aiohttp
import aioredis
import databases

from config import config

redis: aioredis.Redis = aioredis.from_url("redis://localhost")

url = databases.DatabaseURL(
    "mysql+asyncmy://{username}:{password}@{host}:3306/{db}".format(
        username=config.sql_user,
        password=config.sql_pass,
        host=config.sql_host,
        db=config.sql_db,
    ),
)
database: databases.Database = databases.Database(url)

http: aiohttp.ClientSession
