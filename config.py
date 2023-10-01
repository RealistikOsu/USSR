from __future__ import annotations

import logging

from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings

config = Config(".env")

APP_PORT = config("APP_PORT", cast=int)

LOG_LEVEL = config("LOG_LEVEL", cast=int, default=logging.WARNING)

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

DATA_DIR = config("DATA_DIR", default=".data")  # TODO: where should this go?

DIRECT_URL = config("DIRECT_URL", default="https://catboy.best/api")

API_KEYS_POOL: list[str] = list(config("API_KEYS_POOL", cast=CommaSeparatedStrings))

ALLOW_CUSTOM_CLIENTS = config("ALLOW_CUSTOM_CLIENTS", cast=bool)

SRV_URL = config("SRV_URL", default="akatsuki.gg")
SRV_NAME = config("SRV_NAME", default="osu!Akatsuki")

DISCORD_ADMIN_HOOK = config("DISCORD_ADMIN_HOOK")

BOT_USER_ID = config("BOT_USER_ID", cast=int)
FOKABOT_KEY = config("FOKABOT_KEY")

AWS_REGION = config("AWS_REGION")
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
AWS_ENDPOINT_URL = config("AWS_ENDPOINT_URL")
AWS_BUCKET_NAME = config("AWS_BUCKET_NAME")

FTP_HOST = config("FTP_HOST", default=None)
FTP_PORT = config("FTP_PORT", cast=int, default=None)
FTP_USER = config("FTP_USER", default=None)
FTP_PASS = config("FTP_PASS", default=None)

AMQP_HOST = config("AMQP_HOST")
AMQP_PORT = config("AMQP_PORT", cast=int)
AMQP_USER = config("AMQP_USER")
AMQP_PASS = config("AMQP_PASS")

PERFORMANCE_SERVICE_URL = config("PERFORMANCE_SERVICE_URL")

AMPLITUDE_API_KEY = config("AMPLITUDE_API_KEY")
