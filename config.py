from __future__ import annotations

import logging

from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings

config = Config(".env")

APP_HOST = config("APP_HOST")
APP_PORT = config("APP_PORT", cast=int)

LOG_LEVEL = config("LOG_LEVEL", cast=int, default=logging.WARNING)
CODE_HOTRELOAD = config("CODE_HOTRELOAD", cast=bool, default=False)

WRITE_DB_HOST = config("WRITE_DB_HOST")
WRITE_DB_PORT = config("WRITE_DB_PORT", cast=int)
WRITE_DB_USER = config("WRITE_DB_USER")
WRITE_DB_PASS = config("WRITE_DB_PASS")
WRITE_DB_NAME = config("WRITE_DB_NAME")

READ_DB_HOST = config("READ_DB_HOST")
READ_DB_PORT = config("READ_DB_PORT", cast=int)
READ_DB_USER = config("READ_DB_USER")
READ_DB_PASS = config("READ_DB_PASS")
READ_DB_NAME = config("READ_DB_NAME")

DIRECT_URL = config("DIRECT_URL", default="https://catboy.best/api")

API_KEYS_POOL: list[str] = list(config("API_KEYS_POOL", cast=CommaSeparatedStrings))

ALLOW_CUSTOM_CLIENTS = config("ALLOW_CUSTOM_CLIENTS", cast=bool)

SRV_URL = config("SRV_URL", default="akatsuki.gg")
SRV_NAME = config("SRV_NAME", default="osu!Akatsuki")

DISCORD_ADMIN_HOOK = config("DISCORD_ADMIN_HOOK")
BEATMAP_UPDATE_HOOK = config("BEATMAP_UPDATE_HOOK")

BOT_USER_ID = config("BOT_USER_ID", cast=int)
FOKABOT_KEY = config("FOKABOT_KEY")

AWS_REGION = config("AWS_REGION", default=None)
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default=None)
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default=None)
AWS_ENDPOINT_URL = config("AWS_ENDPOINT_URL", default=None)
AWS_BUCKET_NAME = config("AWS_BUCKET_NAME", default=None)

AMQP_HOST = config("AMQP_HOST", default=None)
amqp_port = config("AMQP_PORT", default=None)  # optional int
if amqp_port:
    AMQP_PORT: int | None = int(amqp_port)
else:
    AMQP_PORT = None
AMQP_USER = config("AMQP_USER", default=None)
AMQP_PASS = config("AMQP_PASS", default=None)

BANCHO_SERVICE_URL = config("BANCHO_SERVICE_URL")

PERFORMANCE_SERVICE_URL = config("PERFORMANCE_SERVICE_URL")

AMPLITUDE_API_KEY = config("AMPLITUDE_API_KEY", default=None)

REDIS_HOST = config("REDIS_HOST")
REDIS_PORT = config("REDIS_PORT", cast=int)
REDIS_USER = config("REDIS_USER")
REDIS_DB = config("REDIS_DB")
REDIS_PASS = config("REDIS_PASS")
REDIS_USE_SSL = config("REDIS_USE_SSL", cast=bool)

SCORE_SUBMISSION_ROUTING_KEYS: list[str] = list(
    config("SCORE_SUBMISSION_ROUTING_KEYS", cast=CommaSeparatedStrings),
)
