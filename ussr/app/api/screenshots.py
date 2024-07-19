from __future__ import annotations

import random
import string

import app.state
import app.utils
import logger
import settings
from app.models.user import User
from app.objects.path import Path
from app.usecases.user import authenticate_user
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import Header
from fastapi import Query
from fastapi import UploadFile

SS_DELAY = 10  # Seconds per screenshot.
FS_LIMIT = 500_000  # Rosu screenshots don't exceed this.
ERR_RESP = "https://c.ussr.pl/"  # We do a lil trolley.
SS_NAME_LEN = 8

SS_PATH = Path(settings.DATA_SCREENSHOT_DIRECTORY)


async def is_ratelimit(ip: str) -> bool:
    """Checks if an IP is ratelimited from taking screenshots. If not,
    it establishes the limit in Redis."""

    rl_key = "ussr:ss_limit:" + ip
    if await app.state.services.redis.get(rl_key):
        return True

    await app.state.services.redis.setex(rl_key, SS_DELAY, 1)
    return False


AV_CHARS = string.ascii_letters + string.digits


def gen_rand_str(len: int) -> str:
    return "".join(random.choice(AV_CHARS) for _ in range(len))


async def upload_screenshot(
    user: User = Depends(authenticate_user(Form, "u", "p")),
    screenshot_file: UploadFile = File(None, alias="ss"),
    user_agent: str = Header(...),
    x_forwarded_for: str = Header(...),
):
    if not await app.utils.check_online(user.id):
        logger.error(f"{user} tried to upload a screenshot while offline")
        return ERR_RESP

    if user_agent != "osu!":
        logger.error(f"{user} tried to upload a screenshot using a bot")
        return ERR_RESP

    if await is_ratelimit(x_forwarded_for):
        logger.error(f"{user} tried to upload a screenshot while ratelimited")
        return ERR_RESP

    content = await screenshot_file.read()
    if content.__sizeof__() > FS_LIMIT:
        return ERR_RESP

    if content[6:10] in (b"JFIF", b"Exif"):
        ext = "jpeg"
    elif content.startswith(b"\211PNG\r\n\032\n"):
        ext = "png"
    else:
        logger.error(f"{user} tried to upload unknown extension file")
        return ERR_RESP

    while True:
        file_name = f"{gen_rand_str(SS_NAME_LEN)}.{ext}"

        ss_path = SS_PATH / file_name
        if not ss_path.exists():
            break

    ss_path.write_bytes(content)

    logger.info(f"{user} has uploaded screenshot {file_name}")
    return file_name
