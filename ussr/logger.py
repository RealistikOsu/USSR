from __future__ import annotations

import logging
import os
import sys
import time
from enum import IntEnum
from typing import Any
from typing import Optional

from pythonjsonlogger import jsonlogger

DEBUG = "debug" in sys.argv
__all__ = (
    "info",
    "error",
    "warning",
    "debug",
)

logging.basicConfig(
    level="DEBUG",
)

logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)


def info(text: str, *, extra: Optional[dict[str, Any]] = None):
    logger.info(text, extra=extra)


def error(text: str, *, extra: Optional[dict[str, Any]] = None):
    logger.error(text, extra=extra)


def warning(text: str, *, extra: Optional[dict[str, Any]] = None):
    logger.warn(text, extra=extra)


def debug(text: str, *, extra: Optional[dict[str, Any]] = None):
    logger.debug(text, extra=extra)
