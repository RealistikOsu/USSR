import os
from typing import Union

# Orjson is optional and can be replaced 1:1 by the default one. Only use
# it when we have it.
try: from orjson import dump as j_dump
except ImportError: from json import dump as j_dump
try: from orjson import load as j_load
except ImportError: from json import load as j_load

class JsonFile:
    """Assists within working with simple JSON files."""

    def __init__(self, file_name: str, load: bool = True):
        """Loads a Json file `file_name` from disk.
        
        Args:
            file_name (str): The path including the filename of the JSON file
                you would like to load.
            load (str): Whether the JSON file should be loaded immidiately on
                object creation.
        """

        self.file = None
        self.file_name = file_name
        if load and os.path.exists(file_name):
            self.load_file()
    
    def load_file(self) -> None:
        """Reloads the file fully into memory."""

        with open(self.file_name) as f:
            self.file = j_load(f)

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
            j_dump(new_content, f, indent=4)
        self.file = new_content
