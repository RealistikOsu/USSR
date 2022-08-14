#!/usr/bin/env python3.10
from __future__ import annotations

import logging

import uvicorn

import app.usecases.performance
import app.utils
import config

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(message)s",
)


def main() -> int:
    app.usecases.performance.ensure_oppai()
    app.utils.ensure_directory_structure()

    uvicorn.run(
        "app.init_api:asgi_app",
        reload=config.LOG_LEVEL == logging.DEBUG,
        log_level=config.LOG_LEVEL, # type: ignore
        server_header=False,
        date_header=False,
        port=config.APP_PORT,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
