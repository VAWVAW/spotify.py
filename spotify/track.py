import os
import json
import asyncio

from .connection import Connection


class Track:
    def __init__(self, id: str, connection: Connection, cache_dir: str = None, name: str = None):
        self._id = id
        self._uri = "spotify:track:" + id
        self._connection = connection
        self._cache_dir = cache_dir
        self._name = name

        self._album = None
        self._artists = None

    def __dict__(self):
        return {
            "id": self._id,
            "uri": self._uri,
            "name": self._name,
            "album": self._album,
            "artists": self._artists
        }

    @staticmethod
    async def _make_request(id: str, connection: Connection) -> dict:
        endpoint = connection.add_parametrs_to_endpoint(
            "tracks/{id}",
            fields="uri,name,album(id,uri,name),artists(id,uri,name)",
        )

        data = await connection.make_get_request(endpoint, id=id)
        # TODO cache data
        return data

    async def _load_laizy(self):
        # try to load from cache
        if self._cache_dir is not None:
            path = os.path.join(self._cache_dir, "tracks", self._id)
            try:
                # load from cache
                with open(path, "r") as in_file:
                    data = json.load(in_file)
            except FileNotFoundError:
                # request new data
                data = await self._make_request(id=self._id, connection=self._connection)
        else:
            data = await self._make_request(id=self._id, connection=self._connection)

        self._uri = data["uri"]
        self._name = data["name"]
        self._album = data["album"]
        self._artists = data["artists"]

    @property
    async def id(self) -> str:
        return self._id

    @property
    async def uri(self) -> str:
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
    async def artists(self) -> list:
        if self._artists is None:
            await self._load_laizy()
        return self._artists
