from __future__ import annotations

from app.adapters import bancho_service


async def send_message_to_channel(channel: str, message: str) -> None:
    await bancho_service.send_message_to_channel(channel, message)
