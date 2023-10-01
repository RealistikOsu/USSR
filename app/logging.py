from __future__ import annotations

import logging.config

import yaml


def configure_logging() -> None:
    with open("logging.yaml") as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
