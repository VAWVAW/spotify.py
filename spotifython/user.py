from __future__ import annotations

from .abc import Cacheable


class User(Cacheable):
    def __init__(self, uri: URI, cache: Cache, display_name: str = None):
        super().__init__(uri=uri, cache=cache, name=display_name)
        self._playlists = None

    async def to_dict(self) -> dict:
        return {
            "display_name": self._name,
            "uri": str(self._uri),
            "playlists": {
                "items": [
                    {
                        "uri": str(await playlist.uri),
                        "snapshot_id": await playlist.snapshot_id,
                        "name": await playlist.name
                    }
                    for playlist in self._playlists
                ]
            }
        }

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._name = data["display_name"]

        self._playlists = []
        for playlist in data["playlists"]["items"]:
            self._playlists.append(self._cache.get_playlist(
                uri=URI(playlist["uri"]),
                name=playlist["name"],
                snapshot_id=playlist["snapshot_id"]
            ))

    @staticmethod
    async def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "users/{user_id}".format(user_id=uri.id),
            fields="display_name,uri"
        )
        base = await connection.make_request("GET", endpoint)

        # get playlists
        offset = 0
        limit = 50
        endpoint = connection.add_parameters_to_endpoint(
            "users/{userid}/playlists".format(userid=uri.id),
            offset=offset,
            limit=limit,
            fields="items(uri,name,snapshot_id)"
        )

        data = await connection.make_request("GET", endpoint)
        # check for long data that needs paging
        if data["next"] is not None:
            while True:
                endpoint = connection.add_parameters_to_endpoint(
                    "users/{userid}/playlists".format(userid=uri.id),
                    offset=offset,
                    limit=limit,
                    fields="items(uri,name,snapshot_id)"
                )
                offset += limit
                extra_data = await connection.make_request("GET", endpoint)
                data["items"] += extra_data["items"]

                if extra_data["next"] is None:
                    break
        base["playlists"] = data

        return base

    @property
    async def display_name(self) -> str:
        if self._name is None:
            await self._cache.load(await self.uri)
        return self._name

    @property
    async def playlists(self) -> list[Playlist]:
        if self._playlists is None:
            await self._cache.load(await self.uri)
        return self._playlists.copy()


class Me(User):
    # noinspection PyMissingConstructor
    def __init__(self, cache: Cache):
        assert isinstance(cache, Cache)
        self._uri = None
        self._cache = cache
        self._playlists = None

    @staticmethod
    async def make_request(uri: (URI, None), connection: Connection) -> dict:
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "me",
            fields="display_name,uri"
        )
        base = await connection.make_request("GET", endpoint)

        # get playlists
        offset = 0
        limit = 50
        endpoint = connection.add_parameters_to_endpoint(
            "me/playlists",
            offset=offset,
            limit=limit,
            fields="items(uri,name,snapshot_id)"
        )

        data = await connection.make_request("GET", endpoint)
        # check for long data that needs paging
        if data["next"] is not None:
            while True:
                endpoint = connection.add_parameters_to_endpoint(
                    "me/playlists",
                    offset=offset,
                    limit=limit,
                    fields="items(uri,name,snapshot_id)"
                )
                offset += limit
                extra_data = await connection.make_request("GET", endpoint)
                data["items"] += extra_data["items"]

                if extra_data["next"] is None:
                    break
        base["playlists"] = data

        return base

    def load_dict(self, data: dict):
        assert isinstance(data, dict)

        self._uri = URI(data["uri"])
        self._name = data["display_name"]

        self._playlists = []
        for playlist in data["playlists"]["items"]:
            self._playlists.append(self._cache.get_playlist(
                uri=URI(playlist["uri"]),
                name=playlist["name"],
                snapshot_id=playlist["snapshot_id"]
            ))

    @property
    async def display_name(self) -> str:
        if self._name is None:
            await self._cache.load_me()
        return self._name

    @property
    async def playlists(self) -> list[Playlist]:
        if self._playlists is None:
            await self._cache.load_me()
        return self._playlists.copy()

    @property
    async def name(self) -> str:
        if self._name is None:
            await self._cache.load_me()
        return self._name


from .playlist import Playlist
from .cache import Cache
from .uri import URI
from .connection import Connection


