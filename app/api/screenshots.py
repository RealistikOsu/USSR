from __future__ import annotations

import logging
import random
import string
import sys

from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import Header
from fastapi import Response
from fastapi import UploadFile

import app.state
import config
from app import job_scheduling
from app.adapters import amplitude
from app.adapters import s3
from app.models.user import User
from app.usecases.user import authenticate_user

SS_DELAY = 10  # Seconds per screenshot.
FS_LIMIT = 500_000
SS_NAME_LEN = 8


async def should_ratelimit_ip(client_ip_address: str) -> bool:
    """Checks if an IP is ratelimited from taking screenshots. If not,
    it establishes the limit in Redis."""

    redis_key = f"less:ss_limit:{client_ip_address}"
    if await app.state.services.redis.get(redis_key):
        return True

    await app.state.services.redis.setex(redis_key, SS_DELAY, 1)
    return False


AV_CHARS = string.ascii_letters + string.digits


def gen_rand_str(len: int) -> str:
    return "".join(random.choice(AV_CHARS) for _ in range(len))


async def fetch_screenshot(file_path: str) -> Response:
    """Fetches a screenshot from the S3 bucket."""

    if ".." in file_path or "/" in file_path:
        return Response(b"")

    return Response(
        await s3.download(file_path, "screenshots"),
        media_type="image/png",
    )


async def upload_screenshot(
    user: User = Depends(authenticate_user(Form, "u", "p")),
    screenshot_file: UploadFile = File(None, alias="ss"),
    client_user_agent: str = Header(..., alias="User-Agent"),
    client_ip_address: str = Header(..., alias="X-Real-IP"),
) -> Response:
    if not await app.usecases.user.user_is_online(user.id):
        logging.error(f"{user} tried to upload a screenshot while offline")
        return Response(b"https://akatsuki.gg/")

    if client_user_agent != "osu!":
        logging.error(f"{user} tried to upload a screenshot using a bot")
        return Response(b"https://akatsuki.gg/")

    if await should_ratelimit_ip(client_ip_address):
        logging.error(f"{user} tried to upload a screenshot while ratelimited")
        return Response(b"https://akatsuki.gg/")

    content = await screenshot_file.read()

    if sys.getsizeof(content) > FS_LIMIT:
        return Response(b"https://akatsuki.gg/")

    if content[6:10] in (b"JFIF", b"Exif"):
        ext = "jpeg"
    elif content.startswith(b"\211PNG\r\n\032\n"):
        ext = "png"
    else:
        logging.error(f"{user} tried to upload unknown extension file")
        return Response(b"https://akatsuki.gg/")

    file_name = f"{gen_rand_str(SS_NAME_LEN)}.{ext}"

    # TODO: background with retry policy
    await s3.upload(content, file_name, "screenshots")

    if config.AMPLITUDE_API_KEY:
        job_scheduling.schedule_job(
            amplitude.track(
                event_name="upload_screenshot",
                user_id=str(user.id),
                device_id=None,
                event_properties={
                    "file_name": file_name,
                    "file_size": len(content),
                    "url": f"https://osu.akatsuki.pw/ss/{file_name}",
                },
            ),
        )

    logging.info(f"{user} has uploaded screenshot {file_name}")
    return Response(file_name.encode())
