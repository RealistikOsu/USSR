# Support for ripple's pubsub handlers. These are featured in **all** ripple
# based servers.
from globs.caches import name

try: from orjson import loads as j_load
except ImportError: from json import loads as j_load

async def __update_singular(md5: str) -> None:
    """Updates a singular map using data from the osu API."""

async def beatmap_update_pubsub(data) -> None:
    """Handler for the pubsub event `lets:beatmap_updates`.
    
    Forces a beatmap to be updated straight form the osu!api.

    Message:
        Takes JSON formatted data of either of these structures.
        For single map updates:
        ```json
        {
            "id": int,
        }
        ```
        For entire set updates:
        ```json
        {
            "set_id": int
        }
        ```
    """

    # Parse JSON formatted data.
    j_data = j_load(data)

async def username_change_pubsub(data):
    """
    Handles the Redis pubsub event `peppy:change_username`.
    It handles the update of the username cache.
    """

    # Parse JSON formatted data.
    j_data = j_load(data)

    user_id = int(j_data["userID"])

    await name.load_from_id(user_id)
