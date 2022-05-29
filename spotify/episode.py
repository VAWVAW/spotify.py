from .abc import Playable
from .uri import URI
from .cache import Cache
from .connection import Connection


class Episode(Playable):
    def __init__(self, uri: URI, cache: Cache, name: str = None):
        super().__init__(uri=uri, cache=cache, name=name)

    async def to_dict(self) -> dict:
        return {
            "uri": str(self._uri),
            "name": self._name
        }

    @staticmethod
    async def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "episodes/{id}".format(id=uri.id),
            fields="uri,name"
        )
        return await connection.make_request("GET", endpoint)

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == dict["uri"]

        self._name = data["name"]
