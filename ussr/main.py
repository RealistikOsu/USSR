#!/usr/bin/env python3.9
from __future__ import annotations

import logging
import sys


import app.utils
import logger
import settings
import ddtrace
import uvicorn
import uvloop

uvloop.install()

DEBUG = "debug" in sys.argv


def main() -> int:
    ddtrace.patch_all()

    uvicorn.run(
        "app.init_api:asgi_app",
        reload=DEBUG,
        log_level=logging.WARNING,
        server_header=False,
        date_header=False,
        host="0.0.0.0",
        port=settings.HTTP_PORT,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
