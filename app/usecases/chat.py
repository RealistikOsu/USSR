from __future__ import annotations

from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_exponential

import app.state.services
import config
from app.reliability import retry_if_exception_network_related


@retry(
    retry=retry_if_exception_network_related(),
    wait=wait_exponential(),
    stop=stop_after_attempt(10),
    reraise=True,
)
async def send_message_to_channel(channel: str, message: str) -> None:
    response = await app.state.services.http_client.get(
        f"{config.BANCHO_SERVICE_URL}/api/v1/fokabotMessage",
        params={
            "to": channel,
            "msg": message,
            "k": config.FOKABOT_KEY,
        },
        timeout=2,
    )
    response.raise_for_status()
