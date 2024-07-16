from __future__ import annotations

from app.adapters import bancho_service


async def send_message_to_channel(
    *,
    channel: str,
    message: str,
    timeout: float = 15.0,
) -> None:
    await bancho_service.send_message_to_channel(
        channel=channel,
        message=message,
        timeout=timeout,
    )
