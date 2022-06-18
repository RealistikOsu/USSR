from __future__ import annotations

import os

import logger

OPPAI_DIRS = (
    "oppai-ap",
    "oppai-rx",
)


def ensure_oppai() -> None:
    for dir in OPPAI_DIRS:
        if not os.path.exists(dir):
            logger.error(f"Oppai folder {dir} does not exist!")
            raise RuntimeError

        if not os.path.exists(f"{dir}/liboppai.so"):
            logger.warning(f"Oppai ({dir}) not built, building...")
            os.system(f"cd {dir} && chmod +x libbuild && ./libbuild && cd ..")
