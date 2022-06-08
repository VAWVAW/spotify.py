from .abc import PlayContext
from .uri import URI
from .cache import Cache
from .connection import Connection
from .track import Track
from .artist import Artist


class Album(PlayContext):
    def __init__(self, uri: URI, cache: Cache, name: str = None):
        super().__init__(uri=uri, cache=cache, name=name)

        self._artists = None
        self._items = None
        self._images = None

    async def to_dict(self) -> dict:
        return {
            "uri": str(self._uri),
            "name": self._name,
            "images": self._images,
            "artists": [
                {
                    "uri": str(await artist.uri),
                    "name": await artist.name
                }
                for artist in self._artists
            ],
            "tracks": {
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
        assert uri.type == "album"

        offset = 0
        limit = 50
        endpoint = connection.add_parameters_to_endpoint(
            "albums/{id}".format(id=uri.id),
            offset=offset,
            limit=limit
        )

        data = await connection.make_request("GET", endpoint)

        # check for long data that needs paging
        if data["tracks"]["next"] is not None:
            while True:
                offset += limit
                endpoint = connection.add_parameters_to_endpoint(
                    "albums/{id}/tracks".format(id=uri.id),
                    offset=offset,
                    limit=limit
                )
                extra_data = await connection.make_request("GET", endpoint)
                data["tracks"]["items"] += extra_data["items"]

                if extra_data["next"] is None:
                    break
        return data

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._name = data["name"]
        self._images = data["images"]
        self._items = []
        self._artists = []

        for track in data["tracks"]["items"]:
            if track is None:
                continue
            self._items.append(self._cache.get_track(uri=URI(track["uri"]), name=track["name"]))

        for artist in data["artists"]:
            if artist is None:
                continue
            self._items.append(self._cache.get_artist(uri=URI(artist["uri"]), name=artist["name"]))

    @property
    async def tracks(self) -> list[Track]:
        if self._items is None:
            await self._cache.load(uri=self._uri)
        return self._items.copy()

    @property
    async def artists(self) -> list[Artist]:
        if self._artists is None:
            await self._cache.load(uri=self._uri)
        return self._artists.copy()

    @property
    async def images(self) -> list[dict[str, (str, int, None)]]:
        if self._images is None:
            await self._cache.load(uri=self._uri)
        return self._images.copy()

    # TODO add search
