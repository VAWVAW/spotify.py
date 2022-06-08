from .abc import Cacheable
from .cache import Cache
from .connection import Connection
from .uri import URI


class Artist(Cacheable):
    def __init__(self, uri: URI, cache: Cache, name: str = None):
        super().__init__(uri=uri, cache=cache, name=name)

    async def to_dict(self) -> dict:
        return {
            "name": self._name,
            "uri": str(self._uri)
        }

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._name = data["name"]

    @staticmethod
    async def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "artists/{artist_id}".format(artist_id=uri.id),
            fields="name,uri"
        )
        return await connection.make_request("GET", endpoint)
