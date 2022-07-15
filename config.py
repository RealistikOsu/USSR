from dataclasses import dataclass
from dataclasses import field
from json import dump
from json import loads
from typing import Union
from typing import Optional
from typing import Any
from typing import TypeVar
import os

from logger import debug
from logger import info

__name__ = "ConfigModule"
__author__ = "RealistikDash"
__version__ = "v2.0.0"

T = TypeVar("T")

class ConfigReader:
    """A parent class meant for the easy management, updating and the creation
    of a configuration `JSON` file."""
    
    _json: dict
    updated_keys: Optional[list[str]] = None
    updated: bool = False

    def __init_subclass__(cls, config_path: str = "config.json") -> None:
        """Sets and reads the config child class."""

        super().__init_subclass__()
        cls.read(cls, config_path)

        # Read annotated variables into the class.
        for var_name, key_type in cls.__annotations__.items():
            default = getattr(cls, var_name, None)
            key_val = cls.get_config_attribute(cls, var_name.lower(), default)
            key_val = key_type(key_val)
            setattr(cls, var_name, key_val)

        if cls.updated:
            cls.write(cls, config_path)
            cls.on_finish_update(cls)

    def on_finish_update(self) -> None:
        """Called when the config has just been updated.
        This is meant to be overridden."""

        info(
            "The config has just been updated! Please edit according to your preferences!",
        )
        debug("Keys added: " + ", ".join(self.updated_keys)) # type: ignore

        raise SystemExit(0)
    
    def read(self, file_path: str) -> None:
        """Reads the JSON file and sets it within the object."""
        
        if not os.path.exists(file_path):
            # The updater will handle populating the schema
            self._json = {}
            return

        # Read the file.
        with open(file_path, "r") as f:
            self._json = loads(f.read())
    
    def write(self, file_path: str) -> None:
        """Writes the config into a json file."""
        
        # Contrict the config dict from annotations.
        config_dict = {
            var.lower(): getattr(self, var)
            for var in self.__annotations__.keys()
        }
        
        with open(file_path, "w") as f:
            dump(config_dict, f, indent=4)

    def get_config_attribute(self, key: str, default: Optional[T]=None) -> Optional[T]:
        """Fetches the value of the given key from the config, returning the
        default value."""
        
        value = self._json.get(key)
        
        if value is None:
            if not self.updated_keys:
                self.updated_keys = []
            self.updated = True
            self.updated_keys.append(key)
            return default
        
        return value


# TODO: Notifications for config updates.
class Config(ConfigReader):
    """The main class for the storage of config values.
    These values are read directly from the `config.json` file."""

    PORT: int = 2137
    SQL_HOST: str = "localhost"
    SQL_USER: str = "root"
    SQL_DB: str = "ripple"
    SQL_PASS: str = "db password"
    DATA_DIR: str = ".data"
    DIRECT_URL: str = "https://catboy.best/api"
    API_KEYS_POOL: list = ["keys here"]
    CUSTOM_CLIENTS: bool = False
    SRV_URL: str = "https://ussr.pl"
    SRV_NAME: str = "RealistikOsu"
    SRV_VERIFIED_BADGE: int = 1005
    DISCORD_FIRST_PLACE: str = ""
    DISCORD_ADMIN_HOOK: str = ""
    PP_CAP_VN: int = 700
    PP_CAP_RX: int = 1200
    PP_CAP_AP: int = 1200
    WS_WRITE_KEY: str = ""
    BOT_USER_ID: int = 999


config = Config()
