from libs.files import JsonFile
from logger import info, debug

__name__ = "ConfigModule"
__author__ = "RealistikDash"
__version__ = "v2.0.0"

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
            var_name = var_name.lower()
            default = getattr(cls, var_name, None)

            # Read the key.
            key_val = cls.read_json(cls, var_name, default)

            # Force it to be the sepcified type.
            key_val = key_type(key_val)

            # Set the attribute.
            setattr(cls, var_name.upper(), key_val)

        if cls.updated:
            cls.on_finish_update(cls, cls.updated_keys)
    
    def on_finish_update(self, keys_updated: list):
        """Called when the config has just been updated.
        This is meant to be overridden."""

        info("The config has just been updated! Please edit according to your preferences!")
        debug("Keys added: " + ", ".join(keys_updated))
        raise SystemExit(0)
    
    def read_json(self, key: str, default = None):
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

    PORT: int                = 2137
    SQL_HOST: str            = "localhost"
    SQL_USER: str            = "root"
    SQL_DB: str              = "ripple"
    SQL_PASS: str            = "db password"
    DATA_DIR: str            = ".data"
    DIRECT_URL: str          = "https://api.chimu.moe/"
    API_KEYS_POOL: list      = ["keys here"]
    CUSTOM_CLIENTS: bool     = False # Allow custom clients on
    SRV_URL: str             = "https://ussr.pl"
    SRV_NAME: str            = "RealistikOsu"
    SRV_VERIFIED_BADGE: int  = 1005
    DISCORD_FIRST_PLACE: str = ""
    DISCORD_ADMIN_HOOK: str  = ""
    PP_CAP_VN: int           = 700
    PP_CAP_RX: int           = 1200
    PP_CAP_AP: int           = 1200

config = Config()
