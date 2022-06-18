from __future__ import annotations

import os
import sys
import time
from enum import IntEnum
from functools import cache

DEBUG = "debug" in sys.argv
__all__ = (
    "info",
    "error",
    "warning",
    "debug",
)

# https://github.com/cmyui/cmyui_pkg/blob/master/cmyui/logging.py#L20-L45
class Ansi(IntEnum):
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37

    GRAY = 90
    LRED = 91
    LGREEN = 92
    LYELLOW = 93
    LBLUE = 94
    LMAGENTA = 95
    LCYAN = 96
    LWHITE = 97

    RESET = 0

    @cache
    def __repr__(self) -> str:
        return f"\x1b[{self.value}m"


def formatted_date() -> str:
    return time.strftime("%d-%m-%Y %H:%M:%S", time.localtime())


def _log(content: str, action: str, colour: Ansi = Ansi.WHITE):
    timestamp = formatted_date()
    sys.stdout.write(  # This is mess but it forms in really cool log.
        f"\x1b[90m[{timestamp} - {colour!r}\033[1"
        f"m{action}\033[0m\x1b[90m]: \x1b[94m{content}\x1b[0m\n",
    )


def info(text: str):
    _log(text, "INFO", Ansi.GREEN)


def error(text: str):
    write_log_file(text)
    _log(text, "ERROR", Ansi.RED)


def warning(text: str):
    _log(text, "WARNING", Ansi.BLUE)


def debug(text: str):
    if DEBUG:
        _log(text, "DEBUG", Ansi.WHITE)


def ensure_log_file():
    """Ensures that a log file is present that can be written to."""

    if not os.path.exists("err.log"):
        os.mknod("err.log")


def write_log_file(msg: str, timestamp: bool = True):
    """Appends a message to the log file."""

    with open("err.log", "a+") as f:
        if timestamp:
            f.write(f"[{formatted_date()}] {msg}\n")
        else:
            f.write(msg)
