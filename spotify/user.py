from .connection import Connection
from .cache import Cache
from .uri import URI


class User:
    def __init__(self, uri: URI, connection: Connection, cache: Cache, display_name: str = None):
        self._uri = uri
        self._connection = connection
        self._cache = cache
        self._display_name = display_name

    def __dict__(self):
        return {
            "display_name": self._display_name,
            "uri": str(self._uri)
            }

    @property
    def uri(self) -> URI:
        return self._uri

    @property
    def display_name(self) -> str:
        return self._display_name
