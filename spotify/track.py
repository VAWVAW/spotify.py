import os
import json

from typing import List

from .connection import Connection
from .cache import Cache
from .uri import URI


class Track:
    def __init__(self, uri: URI, connection: Connection, cache: Cache, name: str = None):
        self._uri = uri
        self._connection = connection
        self._cache = cache
        self._name = name

        self._album = None
        self._artists = None

    async def __dict__(self):
        return {
            "uri": str(self._uri),
            "name": self._name,
            "album": self._album,
            "artists": self._artists
        }

    @staticmethod
    async def _make_request(t_id: str, connection: Connection) -> dict:
        endpoint = connection.add_parameters_to_endpoint(
            "tracks/{id}",
            fields="uri,name,album(id,uri,name),artists(id,uri,name)",
        )

        data = await connection.make_get_request(endpoint, id=t_id)
        return data

    async def _cache_self(self):
        path = os.path.join(self._cache.cache_dir, "tracks", str(self.uri))
        with open(path, "w") as out_file:
            json.dump(await self.__dict__(), out_file)

    async def _load_laizy(self):
        cache_after = False
        # try to load from cache
        if self._cache.cache_dir is not None:
            path = os.path.join(self._cache.cache_dir, "tracks", str(self.uri))
            try:
                # load from cache
                with open(path, "r") as in_file:
                    data = json.load(in_file)
            except FileNotFoundError:
                # request new data
                data = await self._make_request(t_id=self._uri.id, connection=self._connection)
        else:
            data = await self._make_request(t_id=self._uri.id, connection=self._connection)

        self._uri = data["uri"]
        self._name = data["name"]
        self._album = data["album"]
        self._artists = data["artists"]

        if cache_after:
            await self._cache_self()

    @property
    async def uri(self) -> URI:
        return self._uri

    @property
    async def name(self) -> str:
        if self._name is None:
            await self._load_laizy()
        return self._name

    @property
    async def album(self) -> dict:
        if self._album is None:
            await self._load_laizy()
        return self._album

    @property
    async def artists(self) -> List[dict]:
        if self._artists is None:
            await self._load_laizy()
        return self._artists
