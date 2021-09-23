# Support for ripple's pubsub handlers. These are featured in **all** ripple
# based servers.
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
