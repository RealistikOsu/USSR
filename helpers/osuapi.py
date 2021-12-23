# A manager for the osu! api.
from typing import Union
from config import config
from libs.time import Timer
from conn.web_client import simple_get_json
import random
from logger import debug

BASE_URL = "http://old.ppy.sh/api/"

class OsuApiManager:
    """A manager for communcations between the osu!api v1 and the USSR."""

    def __init__(self, base_url: str = BASE_URL) -> None:
        """Configures the osu!api manager.
        
        Args:
            base_url (str): The base url of the osu!api. In the format of 
                "http://url/api/{}".
        """

        self.base_url = base_url
        self.key_pool = config.API_KEYS_POOL
    
    def get_key(self) -> str:
        """A sort of load balancer between the keys to make sure the usage
        of keys is kinda equal."""

        # ADVANCED LOAD BALANCER.
        return random.choice(self.key_pool)
    
    async def make_request(self, endpoint: str, args: dict, 
                           require_key: bool = True) -> Union[list, dict]:
        """Makes a request to the osu!api, handling keys and timeouts.
        
        Args:
            endpoint (str): The osu!api v1 endpoint to make the request to.
            args (dict): A dictionary of get arguments that should be sent 
                with the request.
            require_key (bool): Whether a key from the pool should be inserted
                into the request.
        
        Returns:
            Direct response from the osu!api parsed as a json. Can be a list or
            a dictionary based on the endpoint.
        """

        # Timing the request.
        t = Timer()
        t.start()

        if require_key: 
            args["k"] = self.get_key()

        res = await simple_get_json(BASE_URL + endpoint, args)
        debug(f"osu!api request to {endpoint} took {t.time_str()} seconds.")
        return res
    
    # Common osu!api endpoints.
    async def get_bmap_from_md5(self, md5: str) -> list:
        """Fetches a beatmap from the osu!api and returns the direct response.
        Thin abstraction for `make_request`.
        
        Args:
            md5 (str): The MD5 hash of the `.osu` file for the beatmap.
        
        Returns:
            dict: The direct response from the osu!api.
        """

        return await self.make_request("get_beatmaps", {"k": self.get_key(), 
                                                        "h": md5})
        
    async def get_bmap_from_id(self, bmap_id: int) -> list:
        """Fetches a beatmap from the osu!api using its id, returning the
        direct response.
        
        Args:
            bmap_id (int): The id of the beatmap.
        
        Returns:
            list: The direct response from the osu!api.
        """

        return await self.make_request("get_beatmaps", {"k": self.get_key(), 
                                                        "b": bmap_id})
