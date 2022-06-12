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
        self._me = None
        self._by_type = {
            "playlist": {},
            "episode": {},
            "track": {},
            "album": {},
            "artist": {},
            "show": {},
            "user": {}
        }

        self._datatypes = {
            "playlist": Playlist,
            "episode": Episode,
            "track": Track,
            "album": Album,
            "artist": Artist,
            "show": Show,
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

    def load(self, uri: URI):
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
                data = element.make_request(uri=uri, connection=self._connection)
                data["fetched"] = True
        else:
            data = element.make_request(uri=uri, connection=self._connection)
            data["fetched"] = True

        try:
            element.load_dict(data)
        except (KeyError, ElementOutdated):
            # maybe cache is outdated
            data = element.make_request(uri=uri, connection=self._connection)
            data["fetched"] = True
            element.load_dict(data)

        # cache if needed
        if data["fetched"] and self._cache_dir is not None:
            path = os.path.join(self._cache_dir, str(uri))
            with open(path, "w") as out_file:
                json.dump(element.to_dict(), out_file)

    def get_me(self) -> Me:
        if self._me is None:
            self._me = Me(cache=self)
        return self._me

    # noinspection PyTypeChecker
    def load_me(self):
        element = self.get_me()

        # try to load from cache
        if self._cache_dir is not None:
            path = os.path.join(self._cache_dir, "me")
            try:
                with open(path, "r") as in_file:
                    data = json.load(in_file)
                    data["fetched"] = False
            except (FileNotFoundError, json.JSONDecodeError):
                # request new data
                data = element.make_request(uri=None, connection=self._connection)
                data["fetched"] = True
        else:
            data = element.make_request(uri=None, connection=self._connection)
            data["fetched"] = True

        try:
            element.load_dict(data)
        except (KeyError, ElementOutdated):
            # maybe cache is outdated
            data = element.make_request(uri=None, connection=self._connection)
            data["fetched"] = True
            element.load_dict(data)

        # cache if needed
        if data["fetched"] and self._cache_dir is not None:
            path = os.path.join(self._cache_dir, "me")
            with open(path, "w") as out_file:
                json.dump(element.to_dict(), out_file)

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

    def get_album(self, uri: URI, name: str = None) -> Album:
        assert isinstance(uri, URI)

        if uri not in self._by_type["playlist"].keys():
            to_add = Album(uri=uri, cache=self, name=name)
            self._by_type["album"][uri] = to_add
            self._by_uri[str(uri)] = to_add
        return self._by_type["album"][uri]

    def get_artist(self, uri: URI, name: str = None) -> Artist:
        assert isinstance(uri, URI)

        if uri not in self._by_type["artist"].keys():
            to_add = Artist(uri=uri, cache=self, name=name)
            self._by_type["artist"][uri] = to_add
            self._by_uri[str(uri)] = to_add
        return self._by_type["artist"][uri]

    def get_user(self, uri: URI, display_name: str = None) -> User:
        assert isinstance(uri, URI)

        if uri not in self._by_type["user"].keys():
            to_add = User(uri=uri, cache=self, display_name=display_name)
            self._by_type["user"][uri] = to_add
            self._by_uri[str(uri)] = to_add
        return self._by_type["user"][uri]

    def get_episode(self, uri: URI, name: str = None) -> Episode:
        assert isinstance(uri, URI)

        if uri not in self._by_type["episode"].keys():
            to_add = Show(uri=uri, cache=self, name=name)
            self._by_type["episode"][uri] = to_add
            self._by_uri[str(uri)] = to_add
        return self._by_type["episode"][uri]

    def get_show(self, uri: URI, name: str = None) -> Show:
        assert isinstance(uri, URI)

        if uri not in self._by_type["show"].keys():
            to_add = Show(uri=uri, cache=self, name=name)
            self._by_type["show"][uri] = to_add
            self._by_uri[str(uri)] = to_add
        return self._by_type["show"][uri]


from .user import User, Me
from .playlist import Playlist
from .episode import Episode
from .track import Track
from .abc import Cacheable
from .artist import Artist
from .album import Album
from .show import Show
