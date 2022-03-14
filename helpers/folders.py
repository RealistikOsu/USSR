"""Created a full dedicated file for 2 poor functions, i know."""
from genericpath import exists
from os.path import isdir
from os import makedirs

from config import config

REQUIRED_FOLDERS = [
    config.DATA_DIR,
    f"{config.DATA_DIR}/replays/",
    f"{config.DATA_DIR}/replays_relax/",
    f"{config.DATA_DIR}/replays_ap/",
    f"{config.DATA_DIR}/maps/",
]


def verify_required_folders() -> bool:
    """Verifies that all required folders for USSR to work properly"""
    if not exists(REQUIRED_FOLDERS[0]):
        return False
    for folder in REQUIRED_FOLDERS:
        if isdir(folder):
            continue
        else:
            return False
    return True


def ensure_required_folders():
    for folder in REQUIRED_FOLDERS:
        makedirs(folder,exist_ok=True)
