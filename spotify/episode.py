from .abc import Playable
from .uri import URI
from .cache import Cache
from .connection import Connection


class Episode(Playable):
    def __init__(self, uri: URI, cache: Cache, name: str = None):
        super().__init__(uri=uri, cache=cache, name=name)
        self._images = None

    async def to_dict(self) -> dict:
        return {
            "uri": str(self._uri),
            "name": self._name,
            "images": self._images
        }

    @staticmethod
    async def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "episodes/{id}".format(id=uri.id),
            fields="uri,name,images"
        )
        return await connection.make_request("GET", endpoint)

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._name = data["name"]
        self._images = data["images"]

    @property
    async def images(self) -> list[dict[str, (str, int, None)]]:
        if self._images is None:
            await self._cache.load(uri=self._uri)
        return self._images.copy()
