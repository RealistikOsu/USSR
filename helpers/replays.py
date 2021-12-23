from libs.crypt import hash_md5, ts_to_utc_ticks
from constants.c_modes import CustomModes
from aiopath import AsyncPath as Path
from libs.bin import BinaryWriter
from objects.score import Score
from typing import Optional
from config import config
from logger import debug
import os

if config.DATA_DIR[0] == "/" or config.DATA_DIR[1] == ":":
    DATA_DIR = Path(config.DATA_DIR)
else:
    DATA_DIR = os.getcwd() / Path(config.DATA_DIR)

def get_replay_path(score_id: int, c_mode: CustomModes) -> Path:
    """Gets the path of a replay with the given ID."""

    suffix = c_mode.to_db_suffix()
    return DATA_DIR / f"replays{suffix}/replay_{score_id}.osr"

async def read_replay(score_id: int, c_mode: CustomModes) -> Optional[bytes]:
    """Reads a replay with the ID from the fs."""

    path = get_replay_path(score_id, c_mode)
    # Check if it exists.
    if not await path.exists():
        return

    return await path.read_bytes()

async def write_replay(score_id: int, rp: bytes, c_mode: CustomModes) -> None:
    """Writes the replay to storage."""

    path = get_replay_path(score_id, c_mode)

    await path.write_bytes(rp)

# Variables used in the headers.
OSU_VERSION = 20211103

async def build_full_replay(s: Score) -> Optional[BinaryWriter]:
    """Builds a full osu! replay featuring headers for download on the web.
    
    Args:
        score_id: The score ID corresponding to the replay.
        c_mode: The custom mode the score was set on.
    """

    # TODO: This is uhh memory intensive...
    # TODO: Maybe do file caching?

    path = get_replay_path(s.id, s.c_mode)

    if not await path.exists():
        debug(f"Replay {s.id}.osr does not exist.")
        return

    rp = await path.read_bytes()
    # What the fuck.
    replay_md5 = hash_md5(
        '{}p{}o{}o{}t{}a{}r{}e{}y{}o{}u{}{}{}'.format(
            s.count_100 + s.count_300, s.count_50, s.count_geki, s.count_katu,
            s.count_miss, s.bmap.md5, s.max_combo, "true" if s.full_combo else "false",
            s.username, s.score, 0, s.mods.value, "true"
        )
    )

    # Build the replay header.
    replay = (BinaryWriter()
        .write_u8_le(s.mode.value)
        .write_i32_le(OSU_VERSION)
        .write_osu_string(s.bmap.md5)
        .write_osu_string(s.username)
        .write_osu_string(replay_md5)
        .write_i16_le(s.count_300)
        .write_i16_le(s.count_100)
        .write_i16_le(s.count_50)
        .write_i16_le(s.count_geki)
        .write_i16_le(s.count_katu)
        .write_i16_le(s.count_miss)
        .write_i32_le(s.score)
        .write_i16_le(s.max_combo)
        .write_u8_le(s.full_combo)
        .write_i32_le(s.mods.value)
        .write_u8_le(0)
        .write_i64_le(ts_to_utc_ticks(s.timestamp))
        .write_i32_le(len(rp))
        .write_raw(rp)
        .write_i64_le(s.id)
    )
    return replay

