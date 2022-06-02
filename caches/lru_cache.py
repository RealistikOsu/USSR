from libs.time import get_timestamp
from typing import (
    Optional,
    TypedDict,
    Union,
    TypeVar,
    Generic,
    Generator,
)

CACHE_KEY = Union[int, str, tuple]
T = TypeVar("T")

class LRUCache(Generic[T]):
    """A key-value LRU cache of max capacity."""

    __slots__ = (
        "_size",
        "_cache",
    )

    def __init__(self, size: int = 500) -> None:
        """Creates an empty LRU cache of max capacity `size`."""

        self._cache: dict[CACHE_KEY, T] = {}
        self._size = size
    
    def __len__(self) -> int:
        """Returns how many items are currently in the cache."""

        return len(self._cache)

    # Private methods.
    def __move_to_front(self, key: CACHE_KEY, obj: T) -> None:
        """Moves an object to the front of the LRU cache."""

        del self._cache[key]

        self.__append_to_front(key, obj)
    
    def __append_to_front(self, key: CACHE_KEY, obj: T) -> None:
        """Appends an item to the front of the LRU cache."""

        self._cache = {
            key: obj,
        } | self._cache
    
    def __remove_outside_capacity(self) -> None:
        """Removes the longest unused cached entries till the capacity is met."""
        cache_keys = list(self._cache.keys())
        while len(self) >= self._size:
            del self._cache[cache_keys[-1]]
            cache_keys.remove(cache_keys[-1])

    # Public methods.
    def cache(self, key: CACHE_KEY, obj: T) -> None:
        """Inserts an object into the cache."""

        self.__append_to_front(key, obj)

        if len(self) >= self._size:
            self.__remove_outside_capacity()

    def get(self, key: CACHE_KEY) -> Optional[T]:
        """Attempts to retrieve an object with the given key. Returns
        None if not found."""

        res = self._cache.get(key)

        if not res:
            return
        
        self.__move_to_front(key, res)
        return res
    
    def drop(self, key: CACHE_KEY) -> bool:
        """Attempts to drop an item from the cache. Returns `bool` of whether
        this has been successful."""

        try:
            del self._cache[key]
            return True
        except KeyError:
            return False
    
    def get_all_items(self) -> Generator[T, None, None]:
        """Returns a generator over all items in the cache."""

        return self._cache.values()
