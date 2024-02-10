from __future__ import annotations

import glob
import json
import logging
import os
from typing import Any

CONFIG_PATH = "config.json"


def load_json(path: str) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def set_cwd() -> None:
    """Sets the CWD to the root USSR dir."""

    os.chdir("../../")


def determine_full_path(path: str) -> str:
    return os.path.join(os.getcwd(), path) if not path.startswith("/") else path


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
    )
    set_cwd()
    if not os.path.exists(CONFIG_PATH):
        logging.error(
            "The config file was not found! Make sure you have generated "
            "it prior to using this migration.",
        )
        return 1

    config = load_json(CONFIG_PATH)
    logging.info("Config successfully loaded!")

    data_dir = determine_full_path(config["data_dir"])
    if not os.path.exists(data_dir):
        logging.error("The data directory within the config file was not found!")
        return 1

    for folder in ("replays_relax", "replays_ap"):
        if not os.path.exists(os.path.join(data_dir, folder)):
            continue

        for path in glob.glob(os.path.join(data_dir, folder, "*.osr")):
            file = os.path.basename(path)
            os.rename(path, os.path.join(data_dir, "replays", file))
            logging.info(f"Moved {file}!")


if __name__ == "__main__":
    raise SystemExit(main())
