import time
import math

def get_timestamp() -> int:
    """Fetches the current UNIX timestamp as an integer."""

    return math.ceil(time.time())

def formatted_date():
    """Returns the current formatted date in the format
    DD/MM/YYYY HH:MM:SS"""
    
    return time.strftime("%d-%m-%Y %H:%M:%S", time.localtime())
