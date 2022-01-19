# Helps coordinating stuff between pep.py and the USSR.
from globals.caches import name
from globals.connections import redis
try: from orjson import dumps as j_dump
except ImportError: from json import dumps as j_dump

async def stats_refresh(user_id: int) -> None:
    """Forces a stats refresh in pep.py for a given user."""

    await redis.publish("peppy:update_cached_stats", user_id)

async def notify(user_id: int, message: str) -> None:
    """Sends an in-game notification to the user."""

    msg = j_dump({
        "userID": user_id,
        "message": message
    })
    await redis.publish("peppy:notification", msg)

async def bot_message(user_id: int, message: str) -> None:
    """Sends a bot message to the user."""
    
    msg = j_dump({
        "to": await name.name_from_id(user_id),
        "message": message
    })
    await redis.publish("peppy:bot_msg", msg)

async def channel_message(chan: str, msg: str) -> None:
    """Sends a bot message to a specific in-game channel."""

    msg = j_dump({
        "to": chan,
        "message": msg,
    })
    await redis.publish("peppy:bot_msg", msg)

async def announce(message: str) -> None:
    """Sends a message in the announcements channel."""

    await channel_message("#announce", message)

async def check_online(user_id: int, ip: str = None) -> bool:
    """Checks if the given `user_id` is online on the bancho server.
    
    Args:
        user_id (int): The database ID of the user to check if online.
        ip (str): If set, it will also be checked if the user is online
            from a given IP.
    """

    key = f"peppy:sessions:{user_id}"

    if ip: return await redis.sismember(key, ip)
    return await redis.exists(key)

async def notify_ban(user_id: int) -> None:
    """Notifies pep.py of a restrict/ban/unban/unrestrict of a user."""

    await redis.publish("peppy:ban", user_id)

async def notify_new_score(score_id: int) -> None:
    """Notifies the API of a new score done by a user.
    
    Args:
        score_id (int): The ID of the score.
    """

    await redis.publish("api:score_submission", score_id)
