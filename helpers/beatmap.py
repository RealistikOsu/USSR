# Helpers for general beatmap functions.
from logger import debug, error
from conn.web_client import simple_get
from aiopath import AsyncPath as Path
from globals.connections import sql
from typing import Optional
from config import config
import os

if config.DATA_DIR[0] == "/" or config.DATA_DIR[1] == ":":
    DIR_MAPS = Path(config.DATA_DIR) / "maps"
else:
    DIR_MAPS = os.getcwd() / Path(config.DATA_DIR) / "maps"

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

OSU_DL_DIR = "http://old.ppy.sh/osu/{id}"

async def fetch_osu_file(bmap_id: int) -> str:
    """Downloads the `.osu` beatmap file to the beatmap storage directory.
    If the file already exists in the given location, nothing is done.

    Returns path to the osu file.
    """

    path = DIR_MAPS / f"{bmap_id}.osu"
    if await path.exists():
        debug(f"osu beatmap file for beatmap {bmap_id} is already cached!")
        return path
    
    debug(f"Downloading `.osu` file for beatmap {bmap_id} to {path} ...")
    m_str = await simple_get(OSU_DL_DIR.format(id= bmap_id))
    if (not m_str) or "<html>" in m_str:
        return error(f"Invalid beatmap .osu response! PP calculation will fail!")

    # Write to file.
    await path.write_text(m_str)
    debug(f"Beatmap cached to {path}!")
    return path

async def delete_osu_file(bmap_id: int):
    """Ensures an `.osu` beatmap file is completely deleted from cache."""

    path = DIR_MAPS / f"{bmap_id}.osu"

    try: await path.unlink()
    except Exception: pass

async def user_rated_bmap(user_id: int, bmap_md5: str) -> bool:
    """Check if a user has already submitted a rating for a beatmap.
    
    Args:
        user_id (int): The user ID.
        bmap_md5 (str): The beatmap MD5 hash.
    
    Returns:
        `True` if the user has already submitted a rating for the beatmap.
        `False` otherwise.
    """

    exists_db = await sql.fetchcol(
        "SELECT 1 FROM beatmaps_rating WHERE user_id = %s AND beatmap_md5 = %s",
        (user_id, bmap_md5)
    )

    return bool(exists_db)

async def add_bmap_rating(user_id: int, bmap_md5: str, rating: int) -> float:
    """Adds a new beatmap rating from a user and recalculates the new average
    rating, returning it.
    
    Note:
        This function does not update the rating values of any of the cached
        beatmap objects.
    
    Args:
        user_id (int): The user ID.
        rating (int): The rating to add.
    
    Returns:
        The new average rating as float.
    """

    await sql.execute(
        "INSERT INTO beatmaps_rating (user_id, rating, beatmap_md5) VALUES (%s, %s, %s)",
        (user_id, rating, bmap_md5)
    )

    new_rating = await sql.fetchcol(
        "SELECT AVG(rating) FROM beatmaps_rating WHERE user_id = %s AND beatmap_md5 = %s",
        (user_id, bmap_md5)
    )

    # Set new value in the beatmaps table.
    await sql.execute(
        "UPDATE beatmaps SET rating = %s WHERE beatmap_md5 = %s LIMIT 1",
        (new_rating, bmap_md5)
    )

    return new_rating
