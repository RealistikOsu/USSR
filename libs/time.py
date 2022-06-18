from __future__ import annotations

import math
import time


class Timer:
    """A simple timer class used to time the execution of code."""

    def __init__(self):
        """Initialises timer for use."""
        self.start_time = 0
        self.end_time = 0

    def start(self) -> Timer:
        """Begins the timer."""
        self.start_time = time.time()
        return self

    def end(self) -> float:
        """Ends the timer and returns final time."""
        self.end_time = time.time()
        return self.end_time - self.start_time

    def get_difference(self) -> float:
        """Returns the difference between start and end"""
        return self.end_time - self.start_time

    def reset(self) -> None:
        """Resets the timer."""
        self.end_time = self.start_time = 0

    def ms_return(self) -> float:
        """Returns difference in 2dp ms."""
        return round((self.end_time - self.start_time) * 1000, 2)

    def time_str(self) -> str:
        """Returns a nicely formatted timing result."""

        time = self.end()
        if time < 1:
            time_str = f"{self.ms_return()}ms"
        else:
            time_str = f"{round(time,2)}s"
        return time_str


def get_timestamp() -> int:
    """Fetches the current UNIX timestamp as an integer."""

    return math.ceil(time.time())


def formatted_date():
    """Returns the current formatted date in the format
    DD/MM/YYYY HH:MM:SS"""

    return time.strftime("%d-%m-%Y %H:%M:%S", time.localtime())
