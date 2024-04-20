from __future__ import annotations

import asyncio
import sys
from typing import Any
from typing import Coroutine
from typing import Generator
from typing import TypeVar
from typing import Union

T = TypeVar("T")

ACTIVE_TASKS: set[asyncio.Task[Any]] = set()


def schedule_job(
    coro: Union[
        Generator[Any, None, T],
        Coroutine[Any, Any, T],
    ],
) -> asyncio.Task[T]:
    """\
    Run a coroutine to run in the background.

    This function is a wrapper around `asyncio.create_task` that adds the task
    to a set of active tasks. This set is used to provide handling of any
    exceptions that occur as well as to wait for all tasks to complete before
    shutting down the application.
    """
    task = asyncio.create_task(coro)
    task.add_done_callback(_handle_task_exception)
    _register_task(task)
    return task


def _register_task(task: asyncio.Task[Any]) -> None:
    ACTIVE_TASKS.add(task)


def _unregister_task(task: asyncio.Task[Any]) -> None:
    ACTIVE_TASKS.remove(task)


def _handle_task_exception(task: asyncio.Task[Any]) -> None:
    _unregister_task(task)

    if task.cancelled():
        return None

    try:
        exception = task.exception()
    except asyncio.InvalidStateError:
        pass
    else:
        if exception is not None:
            sys.excepthook(
                type(exception),
                exception,
                exception.__traceback__,
            )


async def await_running_jobs(
    timeout: float,
) -> tuple[set[asyncio.Task[Any]], set[asyncio.Task[Any]]]:
    """\
    Await all tasks to complete, or until the timeout is reached.

    Returns a tuple of done and pending tasks.
    """
    if not ACTIVE_TASKS:
        return set(), set()

    done, pending = await asyncio.wait(
        ACTIVE_TASKS,
        timeout=timeout,
        return_when=asyncio.ALL_COMPLETED,
    )
    return done, pending
