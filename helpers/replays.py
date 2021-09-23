from consts.c_modes import CustomModes
from typing import Optional
from config import conf
import os

async def read_replay(score_id: int, c_mode: CustomModes) -> Optional[bytes]:
    """Reads a replay with the ID from the fs."""

    suffix = c_mode.to_db_suffix()
    path = conf.dir_replays + f"{suffix}/replay_{score_id}.osr"
    # Check if it exists.
    #if not os.path.exists(path): return
    # TODO: Async file reading.
    with open(path, "rb") as f:
        return f.read()

async def build_full_replay(score_id: int) -> bytes: ...
