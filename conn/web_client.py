# For now a simple wrapper around aiohttp.
# Orjson is optional and can be replaced 1:1 by the default one. Only use
# it when we have it.
try: from orjson import loads as j_load
except ImportError: from json import loads as j_load
import aiohttp

async def simple_get(url: str, args: dict = {}) -> str:
    """Sends a simple `GET` request to `url` with GET args `args` and returns
    the response body as a `str`."""
    async with aiohttp.ClientSession() as s:
        async with s.get(url, params=args) as res:
            return await res.text()
    
async def simple_get_json(url: str, args: dict = {}) -> dict:
    """Sends a simple `GET` request to `url` with GET args `args` and returns
    the response body JSON as `dict`."""

    res = await simple_get(url, args)
    return j_load(res)
