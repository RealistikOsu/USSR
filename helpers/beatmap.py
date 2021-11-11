# Helpers for general beatmap functions.
from logger import debug, error
from conn.web_client import simple_get
from globs.conn import sql
from typing import Optional
from config import conf
import os

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

    path = conf.dir_maps + f"/{bmap_id}.osu"
    if os.path.exists(path):
        debug(f"osu beatmap file for beatmap {bmap_id} is already cached!")
        return path
    
    debug(f"Downloading `.osu` file for beatmap {bmap_id} to {path} ...")
    m_str = await simple_get(OSU_DL_DIR.format(id= bmap_id))
    if not m_str:
         return error(f"Invalid beatmap .osu response! PP calculation will fail!")

    # Write to file.
    with open(path, "w") as f: f.write(m_str)
    debug(f"Beatmap cached to {path}!")
    return path

def delete_osu_file(bmap_id: int):
    """Ensures an `.osu` beatmap file is completely deleted from cache."""

    path = conf.dir_maps + f"/{bmap_id}.osu"

    try: os.remove(path)
    except FileNotFoundError: pass
