from .cache import Cache
from .uri import URI
from .cacheable import Cacheable
from .connection import Connection


class User(Cacheable):
    def __init__(self, uri: URI, cache: Cache, display_name: str = None):
        super().__init__(uri=uri, cache=cache, name=display_name)

    def to_dict(self) -> dict:
        return {
            "display_name": self._name,
            "uri": str(self._uri)
        }

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._name = data["display_name"]

    @staticmethod
    async def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "users/{user_id}",
            fields="display_name,uri"
        )
        return await connection.make_get_request(endpoint, user_id=uri.id)

    @property
    def uri(self) -> URI:
        return self._uri

    @property
    def display_name(self) -> str:
        if self._name is None:
            self._cache.load(self.uri)
        return self._name
