"""Created a full dedicated file for 2 poor functions, i know."""
from os.path import isdir
from os import makedirs


REQUIRED_FOLDERS = [
    ".data/",
    ".data/replays/",
    ".data/replays_relax/",
    ".data/replays_ap/",
    ".data/maps/",
]


def verify_required_folders() -> bool:
    """Verifies that all required folders for USSR to work properly"""
    for folder in REQUIRED_FOLDERS:
        if isdir(folder):
            continue
        else:
            return False
    return True


def ensure_required_folders():
    for folder in REQUIRED_FOLDERS:
        makedirs(folder,exist_ok=True)
