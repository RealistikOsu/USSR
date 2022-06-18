from __future__ import annotations

import os

import logger
from config import config

REQUIRED_FOLDERS = (
    config.DATA_DIR,
    f"{config.DATA_DIR}/replays/",
    f"{config.DATA_DIR}/replays_relax/",
    f"{config.DATA_DIR}/replays_ap/",
    f"{config.DATA_DIR}/maps/",
)


def ensure_folders():
    for folder in REQUIRED_FOLDERS:
        if not os.path.exists(folder):
            logger.warning(f"Creating data folder {folder}...")
            os.makedirs(folder, exist_ok=True)
