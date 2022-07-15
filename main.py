#!/usr/bin/env python3.9
from __future__ import annotations

import logging
import sys

import uvicorn
import uvloop

import app.usecases.performance
import app.utils
import logger
from config import config

uvloop.install()

DEBUG = "debug" in sys.argv


def main() -> int:
    logger.ensure_log_file()
    app.usecases.performance.ensure_oppai()
    app.utils.ensure_folders()

    uvicorn.run(
        "app.init_api:asgi_app",
        reload=DEBUG,
        log_level=logging.WARNING,
        server_header=False,
        date_header=False,
        host="127.0.0.1",
        port=config.port,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
