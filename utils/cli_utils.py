# Common functions shared between utilities.
# Hacky way to import main
import sys
sys.path.append(".")
import os
os.chdir("../")

from main import ensure_dependencies, perform_startup
import asyncio

loop = None
def get_loop() -> asyncio.AbstractEventLoop:
    """Creates an async event loop with uvloop if available."""

    # UVloop is handled by main import.
    global loop
    loop = asyncio.get_event_loop()
    return loop

def perform_startup_requirements():
    """Performs the standard startup requirements, including async ones."""
    
    if not loop: get_loop()
    ensure_dependencies()
    loop.run_until_complete(perform_startup(False))

if __name__ == "__main__":
    raise ValueError(
        "cli_utils is not a utility, but a library shared between all of the "
        "USSR utilities."
    )
