# For now a simple wrapper around aiohttp.
# Orjson is optional and can be replaced 1:1 by the default one. Only use
# it when we have it.
try: from orjson import loads as j_load, dumps as j_dump
except ImportError: from json import loads as j_load, dumps as j_dump
from typing import Union
import aiohttp

async def simple_get(url: str, args: dict = {}) -> str:
    """Sends a simple `GET` request to `url` with GET args `args` and returns
    the response body as a `str`."""
    async with aiohttp.ClientSession() as s:
        async with s.get(url, params=args) as res:
            return await res.text()
    
async def simple_get_json(url: str, args: dict = {}) -> Union[list, str]:
    """Sends a simple `GET` request to `url` with GET args `args` and returns
    the response body JSON as `dict`."""

    res = await simple_get(url, args)
    return j_load(res)

#async def simple_post(url: str, data: dict = {}) -> str:
#    """Sends a simple `POST` request to `url` with x-form-data post data 
#    from `data` sent."""
#
#    async with aiohttp.ClientSession() as s:
#        async with s.post(url, data= data, headers= {"Content-Type": "application/json"}) as res:
#            return await res.text()

async def simple_post_json(url: str, data: dict = {}, read_res: bool = True) -> Union[list, str, None]:
    """Sends a simple `POST` request to `url` with json post data 
    from `data` sent. The data is then deserialised as a dictionary or list.
    
    If `read_res` is False, the response will not be read.
    """

    dat_json = j_dump(data).decode()
    async with aiohttp.ClientSession() as s:
        async with s.post(url, data= dat_json, headers= {"Content-Type": "application/json"}) as res:
            return await res.json() if read_res else None
