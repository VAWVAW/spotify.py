from .connection import Connection
from .cache import Cache


class User:
    def __init__(self, u_id: str, connection: Connection, cache: Cache, display_name: str = None):
        self._id = u_id
        self._uri = "spotify:user:" + u_id
        self._connection = connection
        self._cache = cache
        self._display_name = display_name

    def __dict__(self):
        return {
            "id": self._id,
            "display_name": self._display_name,
            "uri": self._uri
            }

    @property
    def id(self) -> str:
        return self._id

    @property
    def uri(self) -> str:
        return self._uri

    @property
    def display_name(self) -> str:
        return self._display_name
