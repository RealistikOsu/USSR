from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

_BOOLEAN_STRINGS = ("true", "1", "yes")
def _parse_bool(value: str) -> bool:
    return value.strip().lower() in _BOOLEAN_STRINGS


def _parse_string_list(value: str) -> list[str]:
    return value.strip().replace(", ", ",").split(",")

# HTTP Configuration
HTTP_PORT = int(os.environ["HTTP_PORT"])

# MySQL Database Configuration
MYSQL_HOST = os.environ["MYSQL_HOST"]
MYSQL_USER = os.environ["MYSQL_USER"]
MYSQL_DATABASE = os.environ["MYSQL_DATABASE"]
MYSQL_PASSWORD = os.environ["MYSQL_PASSWORD"]

# MeiliSearch Configuration
MEILI_DIRECT = _parse_bool(os.environ["MEILI_DIRECT"])
MEILI_URL = os.environ["MEILI_URL"]
MEILI_KEY = os.environ["MEILI_KEY"]

# Directories and URLs
DATA_BEATMAP_DIRECTORY = os.environ["DATA_BEATMAP_DIRECTORY"]
DATA_SCREENSHOT_DIRECTORY = os.environ["DATA_SCREENSHOT_DIRECTORY"]

# API Configuration
API_KEYS_POOL = _parse_string_list(os.environ["API_KEYS_POOL"])
API_FALLBACK_URL = os.environ["API_FALLBACK_URL"]
API_OSU_FALLBACK_URL = os.environ["API_OSU_FALLBACK_URL"]
DIRECT_URL = os.environ["DIRECT_URL"]

# Server Information
PS_DOMAIN = os.environ["SRV_URL"]
PS_NAME = os.environ["SRV_NAME"]
PS_VERIFIED_BADGE = int(os.environ["SRV_VERIFIED_BADGE"])
PS_BOT_USER_ID = int(os.environ["BOT_USER_ID"])
PS_ALLOW_CUSTOM_CLIENTS = _parse_bool(os.environ["CUSTOM_CLIENTS"])

# Discord Configuration
DISCORD_FIRST_PLACE = os.environ["DISCORD_FIRST_PLACE"]
DISCORD_ADMIN_HOOK = os.environ["DISCORD_ADMIN_HOOK"]

# WebSocket Configuration
WS_WRITE_KEY = os.environ["WS_WRITE_KEY"]

# Performance Service Configuration
PERFORMANCE_SERVICE_URL = os.environ["PERFORMANCE_SERVICE_URL"]

# S3 Configuration
S3_ENABLED = _parse_bool(os.environ["S3_ENABLED"])
S3_BUCKET = os.environ["S3_BUCKET"]
S3_REGION = os.environ["S3_REGION"]
S3_ENDPOINT = os.environ["S3_ENDPOINT"]
S3_ACCESS_KEY = os.environ["S3_ACCESS_KEY"]
S3_SECRET_KEY = os.environ["S3_SECRET_KEY"]