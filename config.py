from dataclasses import dataclass, field
from json import dump, loads
from typing import Union

from logger import debug
from logger import info

import os

__name__ = "ConfigModule"
__author__ = "RealistikDash"
__version__ = "v2.0.0"


@dataclass
class JsonFile:
    file_name: str
    file: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Reloads the file fully into memory."""

        if not os.path.exists(self.file_name):
            return

        with open(self.file_name) as f:
            self.file = loads(f.read())

    def get_file(self) -> dict:
        """Returns the loaded JSON file as a dict.
        Returns:
            Contents of the file.
        """
        return self.file

    def write_file(self, new_content: Union[dict, list]) -> None:
        """Writes `new_content` to the target file.
        Args:
            new_content (dict, list): The new content that should be placed
                within the file.
        """

        with open(self.file_name, "w") as f:
            dump(new_content, f, indent=4)

        self.file = new_content


class ConfigReader:
    """A parent class meant for the easy management, updating and the creation
    of a configuration `JSON` file."""

    def __init__(self):
        """Sets placeholder variables."""

        # Set to true if a new value was added to the config.
        self.updated: bool = False
        self.updated_keys: list = []

        # An object around the configuration file.
        self.json: JsonFile = JsonFile("config.json")

    def __init_subclass__(cls, stop_on_update: bool = False):
        """Sets and reads the config child class."""

        cls.__init__(cls)

        # Now we read all of the annotated valiables.
        for var_name, key_type in cls.__annotations__.items():

            # We are checking for a possible default value (in case its a new field)
            default = getattr(cls, var_name, None)

            # Read the key. json is lower case so we have to transform
            key_val = cls.read_json(cls, var_name.lower(), default)

            # Force it to be the sepcified type.
            key_val = key_type(key_val)

            # Set the attribute.
            setattr(cls, var_name, key_val)

        if cls.updated:
            cls.on_finish_update(cls, cls.updated_keys)

    def on_finish_update(self, keys_updated: list):
        """Called when the config has just been updated.
        This is meant to be overridden."""

        info(
            "The config has just been updated! Please edit according to your preferences!",
        )
        debug("Keys added: " + ", ".join(keys_updated))

        raise SystemExit(0)

    def read_json(self, key: str, default=None):
        """Reads a value directly from the json file and returns
        if. If the value is not already in the JSON file, it adds
        it and sets it as `default`.
        Args:
            key (str): The JSON key to fetch the value of.
            default (any): The value for the key to be set to if the
                value is not set.
        Returns:
            Value of the key.
        """

        # Handle a case where the file is empty/not found.
        if self.json.file is None:
            # Set it to an empty dict so it can be handled with the thing below.
            self.json.file = {}

        # Check if the key is present. If not, set it.
        if key not in tuple(self.json.file):
            # Set it so we can check if the key was modified.
            self.updated = True
            self.updated_keys.append(key)
            # Set the value in dict.
            self.json.file[key] = default

            # Write it to the file.
            self.json.write_file(self.json.file)

            # Return default
            return default

        # It exists, just return it.
        return self.json.file[key]


# TODO: Notifications for config updates.
class Config(ConfigReader):
    """The main class for the storage of config values.
    These values are read directly from the `config.json` file."""

    PORT: int  # 7000

    DB_HOST: str  # "localhost"
    DB_USER: str  # "root"
    DB_NAME: str  # "akatsuki"
    DB_PASS: str  # "your_db_password"

    DATA_DIR: str  # ".data"

    DIRECT_URL: str  # "https://catboy.best/api"

    API_KEYS_POOL: list[str]  # ["keys here"]

    ALLOW_CUSTOM_CLIENTS: bool  # False  # Allow custom clients on

    SRV_URL: str  # "akatsuki.pw"
    SRV_NAME: str  # "Akatsuki"

    DISCORD_ADMIN_HOOK: str  # ""

    BOT_USER_ID: int  # 999
    FOKABOT_KEY: str  # ""

    AWS_REGION: str  # "ca-central-1"
    AWS_ACCESS_KEY_ID: str  # "your_access_key_id"
    AWS_SECRET_ACCESS_KEY: str  # "your_secret_access_key"
    AWS_ENDPOINT_URL: str  # f"https://s3.ca-central-1.wasabisys.com"
    AWS_BUCKET_NAME: str  # "akatsuki.pw"


config = Config()
