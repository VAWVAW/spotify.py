from .connection import Connection


class User:
    def __init__(self, id: str, connection: Connection, cache_dir: str = None, display_name: str = None):
        self._id = id
        self._uri = "spotify:user:" + id
        self._connection = connection
        self._cache_dir = cache_dir
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