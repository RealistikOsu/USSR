from __future__ import annotations

import glob
import json
import logging
import os
from typing import Any

CONFIG_PATH = "config.json"
REPLAY_PREFIXES = (
    "",
    "_relax",
    "_ap",
)


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

    # Search for misnamed replays.
    for prefix in REPLAY_PREFIXES:
        replay_path = os.path.join(data_dir, "replays" + prefix)
        logging.info(f"Setting CWD to {replay_path}")
        os.chdir(replay_path)

        # Find all replays to rename.
        rename_replays = filter(
            lambda x: not x.startswith("replay_"), glob.glob("*.osr"),
        )

        for replay_name in rename_replays:
            new_name = f"replay_{replay_name}"
            logging.info(f"Renaming {replay_name} -> {new_name}")
            os.rename(replay_name, new_name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
