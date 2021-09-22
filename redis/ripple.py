# Support for ripple's pubsub handlers. These are featured in **all** ripple
# based servers.

async def beatmap_update_pubsub(data) -> None:
    """Handler for the pubsub event `lets:beatmap_updates`.
    
    Forces a beatmap to be updated straight form the osu!api.
    """

    ...
