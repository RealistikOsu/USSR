from dataclasses import dataclass
from dataclasses import field
from json import load
from json import dump
from typing import Any
import os

from logger import debug
from logger import info

@dataclass
class Config:
    port: int = 2137
    sql_host: str = "localhost"
    sql_user: str = "root"
    sql_db: str = "rosu"
    sql_pass: str = "password"
    data_dir: str = ".data"
    direct_url: str = "https://catboy.best/api"
    api_keys_pool: list[str] = field(default_factory=list)
    custom_clients: bool = False
    srv_url: str = "https://ussr.pl"
    srv_name: str = "RealistikOsu"
    srv_verified_badge: int = 1005
    discord_first_place: str = ""
    discord_admin_hook: str = ""
    pp_cap_vn: int = 700
    pp_cap_rx: int = 1200
    pp_cap_ap: int = 1200
    ws_write_key: str = ""
    bot_user_id: int = 999
    
def read_config_json() -> dict[str, Any]:
    with open("config.json", "r") as f:
        return load(f)
    
def write_config(config: Config):
    with open("config.json", "w") as f:
        dump(config.__dict__, f, indent=4)

def load_config() -> Config:
    """Loads the config from the file, handling config updates.
    
    Note:
        Raises `SystemExit` on config update.
    """
    
    config_dict = {}
    
    if os.path.exists("config.json"):
        config_dict = read_config_json()
    
    # Compare config json attributes with config class attributes
    missing_keys = [
        key for key in Config.__annotations__ if key not in config_dict
    ]
    
    # Remove extra fields
    for key in tuple(config_dict): # Tuple cast is necessary to create a copy of the keys.
        if key not in Config.__annotations__:
            del config_dict[key]
    
    # Create config regardless, populating it with missing keys and removing
    # unnecessary keys.
    config = Config(**config_dict)
    
    if missing_keys:
        info(f"Your config has been updated with {len(missing_keys)} new keys.")
        debug("Missing keys: " + ", ".join(missing_keys))
        write_config(config)
        raise SystemExit(0)
    
    return config

config = load_config()
