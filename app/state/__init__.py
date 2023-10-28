from __future__ import annotations

import asyncio
import logging
from typing import Awaitable
from typing import Callable

from . import cache
from . import services

tasks: set[asyncio.Task] = set()

PUBSUB_HANDLER = Callable[[str], Awaitable[None]]

PUBSUBS: dict[str, PUBSUB_HANDLER] = {}


async def cancel_tasks() -> None:
    logging.info(f"Cancelling {len(tasks)} tasks.")

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)

    loop = asyncio.get_running_loop()
    for task in tasks:
        if not task.cancelled():
            if exception := task.exception():
                loop.call_exception_handler(
                    {
                        "message": "unhandled exception during loop shutdown",
                        "exception": exception,
                        "task": task,
                    },
                )

    logging.info("Cancelled all tasks.")
