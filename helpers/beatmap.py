# Helpers for general beatmap functions.
from globs.conn import sql
from typing import Optional

async def bmap_md5_from_id(bmap_id: int) -> Optional[str]:
    """Attempts to fetch the beatmap MD5 hash for a map stored in the database.
    
    Note:
        If the beatmap is not stored in the database, `None` is returned.
        No osu!API calls are performed here, just an SQL query.
    
    Args:
        bmap_id (int): The beatmap ID for the map.
    
    Returns:
        The MD5 hash for the beatmap `.osu` file if found in the MySQL
            database.
        Else `None`.
    """

    return await sql.fetchcol(
        "SELECT beatmap_md5 FROM beatmaps WHERE beatmap_id = %s LIMIT 1",
        (bmap_id,)
    )

async def bmap_get_set_md5s(set_id: int) -> tuple[str]:
    """Fetches all available MD5 hashes for an osu beatmap set in the
    database.
    
    Note:
        No osu!API calls are performed here, just an SQL query.
        Can return empty tuple if none are found.
    
    Args:
        set_id (int): The osu! beatmap set ID.
    
    Returns:
        `tuple` of MD5 hashes.
    """

    return await sql.fetchall(
        "SELECT beatmap_md5 FROM beatmaps WHERE beatmapset_id = %s",
        (set_id,)
    )
