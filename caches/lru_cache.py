# This is an old class taken from GDPyS (made by me) serving as a lru cache.
# The code is not the best and is in need of a rewrite but it works well for
# now and is time tested.
from email.generator import Generator
from libs.time import get_timestamp
from typing import (
    Optional,
    TypedDict,
    Union,
    TypeVar,
    Generic,
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


class CachedObject(TypedDict):
    expire: int
    object: object

class Cache:  # generic class
    """A key-value store implementing LRU eviction."""

    def __init__(self, cache_length: int = 5, cache_limit: int = 500) -> None:
        """Establishes a cache and configures the limits.
        Args:
            cache_length (int): How long (in minutes) each cache lasts before
                being removed
            cache_limit (int): A limit to how many objects can be max cached
                before other objects start being removed.
        """
        self._cache: dict[CACHE_KEY, CachedObject] = {}  # The main cache object.
        self.length = (
            cache_length * 60
        )  # Multipled by 60 to get the length in seconds rather than minutes.
        self._cache_limit = cache_limit

    @property
    def cached_items(self) -> int:
        """Returns an int of the lumber of cached items stored."""

        return len(self._cache)

    def __len__(self) -> int:
        return self.cached_items

    def cache(self, key: CACHE_KEY, cache_obj: object) -> None:
        """Adds an object to the cache."""
        self._cache[key] = {
            "expire": get_timestamp() + self.length,
            "object": cache_obj,
        }
        self.run_checks()

    def drop(self, key: CACHE_KEY) -> None:
        """Removes an object from cache."""
        try:
            del self._cache[key]
        except KeyError:
            # It doesnt matter if it fails. All that matters is that no such object exist and if it doesnt exist in the first place, that's already objective complete.
            pass

    def get(self, key: CACHE_KEY) -> Optional[object]:
        """Retrieves a cached object from cache."""

        # Try to get it from cache.
        curr_obj = self._cache.get(key)

        if curr_obj is not None:
            return curr_obj["object"]

    def remove_all_elements(self, pattern: str) -> None:
        # remove all tuple entries with this as a starter

        for key in self._get_cached_keys():
            if isinstance(key, tuple) and key[0] == pattern:
                self.drop(key)

    def _get_cached_keys(self) -> tuple[CACHE_KEY, ...]:
        """Returns a list of all cache keys currently cached."""
        return tuple(self._cache)

    def _get_expired_cache(self) -> list:
        """Returns a list of expired cache keys."""
        current_timestamp = get_timestamp()
        expired = []
        for key in self._get_cached_keys():
            # We dont want to use get as that  will soon have the ability to make its own objects, slowing this down.
            if self._cache[key]["expire"] < current_timestamp:
                # This cache is expired.
                expired.append(key)
        return expired

    def _remove_expired_cache(self) -> None:
        """Removes all of the expired cache."""
        for key in self._get_expired_cache():
            self.drop(key)

    def _remove_limit_cache(self) -> None:
        """Removes all objects past limit if cache reached its limit."""

        # Calculate how much objects we have to throw away.
        throw_away_count = len(self._get_cached_keys()) - self._cache_limit

        if not throw_away_count:
            # No levels to throw away
            return

        # Get x oldest ids to remove.
        throw_away_ids = self._get_cached_keys()[:throw_away_count]
        for key in throw_away_ids:
            self.drop(key)

    def run_checks(self) -> None:
        """Runs checks on the cache."""
        self._remove_expired_cache()
        self._remove_limit_cache()

    def get_all_items(self):
        """Generator that lists all of the objects currently cached."""

        # return [obj["object"] for _, obj in self._cache.items()]

        # Make it a generator for performance.
        for obj in self._cache.values():
            yield obj["object"]

    def get_all_keys(self):
        """Generator that returns all keys of the keys to the cache."""

        return self._get_cached_keys()
