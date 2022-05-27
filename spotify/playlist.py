import json
import os

from typing import List

from .connection import Connection
from .user import User
from .track import Track
from .cache import Cache


class Playlist:
    def __init__(self, p_id: str, connection: Connection, cache: Cache, name: str = None):
        self._id = p_id
        self._uri = "spotify:playlist:" + p_id
        self._connection = connection
        self._cache = cache
        self._name = name

        self._description = None
        self._owner = None
        self._snapshot_id = None
        self._public = None
        self._items = None

    async def __dict__(self):
        return {
            "id": self._id,
            "uri": self._uri,
            "description": self._description,
            "owner": self._owner.__dict__(),
            "snapshot_id": self._snapshot_id,
            "name": self._name,
            "public": self._public,
            "tracks": {
                "items": [
                    {
                        "added_at": item["added_at"],
                        "track":{
                            "id": await item["track"].id,
                            "name": await item["track"].name
                        }
                    }
                    for item in self._items
                ]
            }
        }

    @staticmethod
    async def _make_request(p_id: str, connection: Connection) -> dict:
        offset = 0
        limit = 100
        endpoint = connection.add_parametrs_to_endpoint(
            "playlists/{playlist_id}",
            fields="uri,description,name,owner(id,display_name),snapshot_id,public,tracks(next,items(added_at,track(id,name,uri)))",
            offset=offset,
            limit=limit
        )

        data = await connection.make_get_request(endpoint, playlist_id=p_id)

        # check for long data that needs paging
        if data["tracks"]["next"] is not None:
            while True:
                offset += limit
                endpoint = connection.add_parametrs_to_endpoint(
                    "playlists/{playlist_id}/tracks",
                    fields="next,items(added_at,track(id,name,uri))",
                    offset=offset,
                    limit=limit
                )
                extra_data = await connection.make_get_request(endpoint, playlist_id=p_id)
                data["tracks"]["items"] += extra_data["items"]

                if extra_data["next"] is None:
                    break

        return data

    async def _cache_self(self):
        path = os.path.join(self._cache.cache_dir, "playlists", self._id)
        with open(path, "w") as out_file:
            json.dump(await self.__dict__(), out_file)

    async def _load_laizy(self):
        cache_after = False
        # try to load from cache
        if self._cache.cache_dir is not None:
            path = os.path.join(self._cache.cache_dir, "playlists", self._id)
            try:
                # load from cache
                with open(path, "r") as in_file:
                    data = json.load(in_file)
            except (FileNotFoundError, json.JSONDecodeError):
                # request new data
                data = await self._make_request(p_id=self._id, connection=self._connection)
                cache_after = True
        else:
            data = await self._make_request(p_id=self._id, connection=self._connection)
            cache_after = True

        self._uri = data["uri"]
        self._name = data["name"]
        self._snapshot_id = data["snapshot_id"]
        self._description = data["description"]
        self._public = data["public"]
        self._owner = self._cache.get_user(u_id=data["owner"]["id"], display_name=data["owner"]["display_name"])
        self._items = []
        for track_to_add in data["tracks"]["items"]:
            if track_to_add["track"] is None:
                continue
            self._items.append({
                "track": self._cache.get_track(t_id=track_to_add["track"]["id"], name=track_to_add["track"]["name"]),
                "added_at": track_to_add["added_at"]
            })

        if cache_after:
            await self._cache_self()

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
    async def description(self) -> str:
        if self._description is None:
            await self._load_laizy()
        return self._description

    @property
    async def owner(self) -> User:
        if self._owner is None:
            await self._load_laizy()
        return self._owner

    @property
    async def snapshow_id(self) -> str:
        if self._snapshot_id is None:
            await self._load_laizy()
        return self._snapshot_id

    @property
    async def public(self) -> bool:
        if self._public is None:
            await self._load_laizy()
        return self._public

    @property
    async def items(self) -> List[Track]:
        if self._items is None:
            await self._load_laizy()
        return self._items

    async def search(self, *strings: str) -> List[Track]:
        if self._items is None:
            await self._load_laizy()
        resutlts = []
        strings = [string.lower() for string in strings]
        for item in self._items:
            song_title = (await item["track"].name).lower()

            do_append = True
            for string in strings:
                # on fail
                if song_title.find(string) == -1:
                    do_append = False
                    break

            if do_append:
                resutlts.append(item["track"])

        return resutlts
