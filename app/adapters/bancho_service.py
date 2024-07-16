from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

import config

bancho_service_http_client = httpx.AsyncClient(base_url=config.BANCHO_SERVICE_URL)


@dataclass
class MatchDetails:
    match_name: str
    match_id: int
    slot_id: int
    game_id: int
    team: int


async def get_player_match_details(user_id: int) -> MatchDetails | None:
    try:
        response = await bancho_service_http_client.get(
            "api/v1/playerMatchDetails",
            params={"id": user_id},
            timeout=5.0,
        )
        response.raise_for_status()
        response_data = response.json()
        if response_data["message"] != "ok":
            return None
        return MatchDetails(
            match_name=response_data["result"]["match_name"],
            match_id=response_data["result"]["match_id"],
            slot_id=response_data["result"]["slot_id"],
            game_id=response_data["result"]["game_id"],
            team=response_data["result"]["team"],
        )
    except Exception:
        logging.exception(
            "Failed to get player match status via bancho-service API",
            extra={"user_id": user_id},
        )
        return None


async def send_message_to_channel(
    *,
    channel: str,
    message: str,
    timeout: float,
) -> None:
    try:
        response = await bancho_service_http_client.get(
            "/api/v1/fokabotMessage",
            params={
                "to": channel,
                "msg": message,
                "k": config.FOKABOT_KEY,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        return None
    except Exception:
        logging.exception(
            "Failed to send chat message via bancho-service API",
            extra={"channel": channel, "chat_message": message},
        )
        return None
