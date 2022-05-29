from typing import List

from .connection import Connection
from .cache import Cache
from .uri import URI
from .abc import Playable
from .artist import Artist


class Track(Playable):
    def __init__(self, uri: URI, cache: Cache, name: str = None):
        super().__init__(uri=uri, cache=cache, name=name)

        self._album = None
        self._artists = None

    async def to_dict(self) -> dict:
        return {
            "uri": str(self._uri),
            "name": self._name,
            "album": self._album,
            "artists": [
                {
                    "uri": str(await artist.uri),
                    "name": await artist.name
                }
                for artist in self._artists
            ]
        }

    @staticmethod
    async def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "tracks/{id}".format(id=uri.id),
            fields="uri,name,album(uri,name),artists(uri,name)",
        )
        return await connection.make_request("GET", endpoint)

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == dict["uri"]

        self._name = data["name"]
        self._album = self._cache.get_album(uri=URI(data["album"]["uri"]), name = data["album"]["name"])
        self._artists = []

        for artist in data["artists"]:
            self._artists.append(self._cache.get_artist(uri=URI(artist["uri"]), name=artist["name"]))

    @property
    async def album(self) -> dict:
        if self._album is None:
            await self._cache.load(uri=self._uri)
        return self._album

    @property
    async def artists(self) -> List[Artist]:
        if self._artists is None:
            await self._cache.load(uri=self._uri)
        return self._artists
