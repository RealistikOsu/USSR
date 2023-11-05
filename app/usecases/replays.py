from __future__ import annotations

import app.state.services
from app.adapters import s3


async def save_replay(score_id: int, replay_data: bytes) -> None:
    if app.state.services.s3_client is not None:
        await s3.upload(replay_data, file_name=f"{score_id}.osr", folder="replays")
        return


async def download_replay(score_id: int) -> bytes | None:
    replay_data = None

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

    return replay_data
