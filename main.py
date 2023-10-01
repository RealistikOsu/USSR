#!/usr/bin/env python3.10
from __future__ import annotations

import uvicorn

import app.logging
import app.usecases.performance
import app.utils
import config


def main() -> int:
    app.utils.ensure_directory_structure()
    uvicorn.run(
        "app.init_api:asgi_app",
        reload=config.CODE_HOTRELOAD,
        log_level=config.LOG_LEVEL,  # type: ignore
        server_header=False,
        date_header=False,
        port=config.APP_PORT,
        access_log=False,
    )
    return 0


if __name__ == "__main__":
    app.logging.configure_logging()
    raise SystemExit(main())
