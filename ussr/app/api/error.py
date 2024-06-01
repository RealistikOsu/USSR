from __future__ import annotations

import asyncio
import time
from typing import Optional

import app.state
import app.usecases
import logger
from app.models.user import User
from fastapi import Form


async def log_user_error(
    user: User,
    stacktrace: Optional[str],
    config: str,
    version: str,
    exe_hash: str,
):
    await app.state.services.database.execute(
        "INSERT INTO client_err_logs (user_id, timestamp, traceback, config, osu_ver, osu_hash) "
        "VALUES (:id, :timestamp, :trace, :cfg, :ver, :hash)",
        {
            "id": user.id,
            "timestamp": int(time.time()),
            "trace": stacktrace,
            "cfg": config,
            "ver": version,
            "hash": exe_hash,
        },
    )


async def error(
    user_id: int = Form(..., alias="i"),
    stacktrace: Optional[str] = Form(None),
    config: str = Form(...),
    version: str = Form(...),
    exehash: str = Form(...),
):
    user = await app.usecases.user.fetch_db_id(user_id)
    if not user:
        return

    logger.info(f"{user} has experienced a client exception!")
    asyncio.create_task(log_user_error(user, stacktrace, config, version, exehash))
