from __future__ import annotations

import os
from typing import Union

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


def make_safe(username: str) -> str:
    return username.rstrip().lower().replace(" ", "_")


TIME_ORDER_SUFFIXES = ["ns", "μs", "ms", "s"]


def format_time(time: Union[int, float]) -> str:
    for suffix in TIME_ORDER_SUFFIXES:
        if time < 1000:
            break

        time /= 1000

    return f"{time:.2f}{suffix}"
