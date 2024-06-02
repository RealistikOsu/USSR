#!/usr/bin/env python3.11
from __future__ import annotations

import atexit

import uvicorn

import app.exception_handling
import app.logging
import app.usecases.performance
import config


def main() -> int:
    app.logging.configure_logging()

    app.exception_handling.hook_exception_handlers()
    atexit.register(app.exception_handling.unhook_exception_handlers)

    uvicorn.run(
        "app.init_api:asgi_app",
        reload=config.CODE_HOTRELOAD,
        log_level=config.LOG_LEVEL,
        server_header=False,
        date_header=False,
        host=config.APP_HOST,
        port=config.APP_PORT,
        access_log=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
