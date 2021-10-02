from imghdr import test_png, test_jpeg
from typing import Union
import os

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

# We only support png and jpeg as they are the only ones used by osu!
ALLOWED_TYPES = ("png", "jpeg")
class Image:
    """A simple class for simple work with images. Supports JPEG and PNG
    image types.
    """
    __slots__ = ("_img", "_file_ext")

    def __init__(self, im: bytes, max_size: int = 0) -> None:
        """Creates an instance of `Image` from image bytes. Supports both
        PNG and JPEG image formats. Provides basic, limited functionality
        working with them.
        
        Args:
            im (bytes): The image raw bytes to work with.
            max_size (int): The maximum size (in bytes) the image can be.
                If size is above that, exception is raised and references
                to image are dropped.
        
        Note:
            Raises ValueError if:
                Unsupported filetype given.
                Filesize is above the limit specified.
        """
        self._img: bytes = im
        self._file_ext = self.__check_type()

        if self._file_ext not in ALLOWED_TYPES:
            raise ValueError("Unsupported filetype given. Only PNG and JPEG supproted.")
        
        if not self.__check_size(max_size):
            raise ValueError("Filesize too large!")
    
    def __check_type(self) -> str:
        """Checks the type of the image we are working with."""

        a = test_jpeg(self._img, None)
        return a if a else test_png(self._img, None)
    
    def __check_size(self, size: int) -> bool:
        """Checks if the image we are working with is below a given size. Else
        immidiately drops reference to it so it can be GC'd."""

        if not size: return True
        res = self._img.__sizeof__() < size
        if not res: del self._img
        return res
    
    # TODO: Maybe async these as they may take a while?
    @classmethod
    def from_path(cls, path: str) -> 'Image':
        """Creates an instance of `Image` using a file, reading it from `path`.
        
        Args:
            path (str): The location of the image on storage.
        """

        with open(path, "rb") as f: return cls(f.read())
    
    def write(self, path: str, name: str) -> None:
        """Writes the image bytes to a file on storage, automatically setting
        the file extension.
        
        Args:
            path (str): The folder in which the file should be saved (NO / SUFFIX).
            name (str): The name of the file that should be created.
        """

        w_path = f"{path}/{name}.{self._file_ext}"
        with open(w_path, "wb") as f: f.write(self._img)
