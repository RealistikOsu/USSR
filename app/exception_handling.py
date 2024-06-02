from __future__ import annotations

import logging
import sys
import threading
from collections.abc import Callable
from types import TracebackType
from typing import Any

ExceptionHook = Callable[
    [type[BaseException], BaseException, TracebackType | None],
    Any,
]
ThreadingExceptionHook = Callable[[threading.ExceptHookArgs], Any]

_default_excepthook: ExceptionHook | None = None
_default_threading_excepthook: ThreadingExceptionHook | None = None


def internal_exception_handler(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
) -> None:
    logging.exception(
        "An unhandled exception occurred",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


def internal_thread_exception_handler(
    args: threading.ExceptHookArgs,
) -> None:
    if args.exc_value is None:  # pragma: no cover
        logging.warning("Exception hook called without exception value.")
        return

    logging.exception(
        "An unhandled exception occurred",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        extra={"thread_vars": vars(args.thread)},
    )


def hook_exception_handlers() -> None:
    global _default_excepthook
    _default_excepthook = sys.excepthook
    sys.excepthook = internal_exception_handler

    global _default_threading_excepthook
    _default_threading_excepthook = threading.excepthook
    threading.excepthook = internal_thread_exception_handler


def unhook_exception_handlers() -> None:
    global _default_excepthook
    if _default_excepthook is not None:
        sys.excepthook = _default_excepthook

    global _default_threading_excepthook
    if _default_threading_excepthook is not None:
        threading.excepthook = _default_threading_excepthook
