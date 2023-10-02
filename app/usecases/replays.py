from __future__ import annotations

import os

from tenacity import retry
from tenacity.stop import stop_after_attempt

import app.state.services
import config
from app.adapters import s3

REPLAYS_DIR = f"{config.DATA_DIR}/replays"


# TODO: better
@retry(stop=stop_after_attempt(7))
async def save_replay(score_id: int, replay_data: bytes) -> None:
    if app.state.services.s3_client is not None:
        await s3.upload(replay_data, file_name=f"{score_id}.osr", folder="replays")
        return

    # use file storage as a backup
    with open(f"{REPLAYS_DIR}/{score_id}.osr", "wb") as f:
        f.write(replay_data)


# TODO: better
@retry(stop=stop_after_attempt(7))
async def download_replay(score_id: int) -> bytes | None:
    if app.state.services.s3_client is not None:
        replay_data = await s3.download(file_name=f"{score_id}.osr", folder="replays")
        if replay_data is not None:
            return replay_data

    if app.state.services.ftp_client is not None:
        replay_data = app.state.services.ftp_client.get(
            f"/replays/replay_{score_id}.osr",
        )
        if replay_data is not None:
            return replay_data

    # use file storage as a backup
    if not os.path.exists(f"{REPLAYS_DIR}/{score_id}.osr"):
        return None

    with open(f"{REPLAYS_DIR}/{score_id}.osr", "rb") as f:
        replay_data = f.read()

    return replay_data
