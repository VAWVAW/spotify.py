from __future__ import annotations

from typing import List

from .cache import Cache
from .uri import URI
from .abc import Cacheable
from .connection import Connection


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
                uri=playlist["uri"],
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
    async def playlists(self) -> List[Playlist]:
        if self._playlists is None:
            await self._cache.load(await self.uri)
        return self._playlists.copy()


from .playlist import Playlist

