# resolve circular dependencies
from __future__ import annotations

import json
import os.path

from .connection import Connection
from .uri import URI
from .errors import ElementOutdated


class Cache:
    def __init__(self, connection: Connection, cache_dir: str = None):
        self._cache_dir = cache_dir
        self._connection = connection
        self._by_uri = {}
        self._by_type = {
            "playlist": {},
            "track": {},
            "user": {}
        }

        self._datatypes = {
            "playlist": Playlist,
            "track": Track,
            "user": User
        }

    @property
    def cache_dir(self) -> str:
        return self._cache_dir

    def get_element(self, uri: URI, name: str = None) -> Cacheable:
        if str(uri) not in self._by_uri.keys():
            # generate element based on type in uri
            to_add = self._datatypes[uri.type](uri=uri, cache=self, name=name)
            self._by_uri[str(uri)] = to_add
            self._by_type[uri.type][str(uri)] = to_add

        return self._by_uri[str(uri)]

    async def load(self, uri: URI):
        assert isinstance(uri, URI)

        element = self.get_element(uri)

        # try to load from cache
        if self._cache_dir is not None:
            path = os.path.join(self._cache_dir, str(uri))
            try:
                with open(path, "r") as in_file:
                    data = json.load(in_file)
                    data["fetched"] = False
            except (FileNotFoundError, json.JSONDecodeError):
                # request new data
                data = await element.make_request(uri=uri, connection=self._connection)
                data["fetched"] = True
        else:
            data = await element.make_request(uri=uri, connection=self._connection)
            data["fetched"] = True

        try:
            element.load_dict(data)
        except (KeyError | ElementOutdated):
            # maybe chache is outdated
            data = await element.make_request(uri=uri, connection=self._connection)
            data["fetched"] = True
            element.load_dict(data)

        # cache if needed
        if data["fetched"] and self._cache_dir is not None:
            path = os.path.join(self._cache_dir, str(uri))
            with open(path, "w") as out_file:
                json.dump(await element.to_dict(), out_file)

    # get cached objects and create them if needed
    def get_track(self, uri: URI, name: str = None) -> Track:
        assert isinstance(uri, URI)

        if uri not in self._by_type["track"].keys():
            to_add = Track(uri=uri, cache=self, name=name)
            self._by_type["track"][str(uri)] = to_add
            self._by_uri[str(uri)] = to_add
        return self._by_type["track"][str(uri)]

    def get_playlist(self, uri: URI, name: str = None, snapshot_id: str = None) -> Playlist:
        assert isinstance(uri, URI)

        if uri not in self._by_type["playlist"].keys():
            to_add = Playlist(uri=uri, cache=self, name=name, snapshot_id=snapshot_id)
            self._by_type["playlist"][uri] = to_add
            self._by_uri[str(uri)] = to_add
        return self._by_type["playlist"][uri]

    def get_user(self, uri: URI, display_name: str = None) -> User:
        assert isinstance(uri, URI)

        if uri not in self._by_type["user"].keys():
            to_add = User(uri=uri, cache=self, display_name=display_name)
            self._by_type["user"][uri] = to_add
            self._by_uri[str(uri)] = to_add
        return self._by_type["user"][uri]


from .playlist import Playlist
from .user import User
from .track import Track
from .cacheable import Cacheable
