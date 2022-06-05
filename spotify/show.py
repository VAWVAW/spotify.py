from .abc import PlayContext
from .uri import URI
from .cache import Cache
from .connection import Connection
from .episode import Episode


class Show(PlayContext):
    def __init__(self, uri: URI, cache: Cache, name: str = None):
        super().__init__(uri=uri, cache=cache, name=name)

        self._items = None
        self._images = None
        self._description = None

    async def to_dict(self) -> dict:
        return {
            "uri": str(self._uri),
            "name": self._name,
            "description": self._description,
            "image": self._images,
            "episodes": {
                "items": [
                    {
                        "uri": str(await item.uri),
                        "name": await item.name
                    }
                    for item in self._items
                ]
            }
        }

    @staticmethod
    async def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)
        assert uri.type == "show"

        offset = 0
        limit = 50
        endpoint = connection.add_parameters_to_endpoint(
            "shows/{id}".format(id=uri.id),
            offset=offset,
            limit=limit
        )

        data = await connection.make_request("GET", endpoint)

        # check for long data that needs paging
        if data["episodes"]["next"] is not None:
            while True:
                offset += limit
                endpoint = connection.add_parameters_to_endpoint(
                    "shows/{id}/episodes".format(id=uri.id),
                    offset=offset,
                    limit=limit
                )
                extra_data = await connection.make_request("GET", endpoint)
                data["episodes"]["items"] += extra_data["items"]

                if extra_data["next"] is None:
                    break
        return data

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._name = data["name"]
        self._images = data["images"]
        self._description = data["description"]
        self._items = []

        for episode in data["episodes"]["items"]:
            if episode is None:
                continue
            self._items.append(self._cache.get_episode(uri=URI(episode["uri"]), name=episode["name"]))

    @property
    async def episodes(self) -> list[Episode]:
        if self._items is None:
            await self._cache.load(uri=self._uri)
        return self._items.copy()

    @property
    async def images(self) -> list[dict[str, (str, int, None)]]:
        if self._images is None:
            await self._cache.load(uri=self._uri)
        return self._images.copy()

    @property
    async def description(self) -> str:
        if self._description is None:
            await self._cache.load(uri=self._uri)
        return self._description
