# resolve circular dependencies
from __future__ import annotations

import json
import os.path
import logging
from typing import Type

from .connection import Connection
from .errors import ElementOutdated

log = logging.getLogger(__name__)


class Cache:
    def __init__(self, connection: Connection, cache_dir: str = None):
        self._cache_dir = cache_dir
        self._connection = connection
        self._by_uri = {}
        self._me = None
        self._saved_tracks = None
        self._by_type = {
            Playlist: {},
            Episode: {},
            Track: {},
            Album: {},
            Artist: {},
            Show: {},
            SavedTracks: {},
            User: {}
        }

    @property
    def cache_dir(self) -> str:
        return self._cache_dir

    def get_element(self, uri: URI, name: str = None, **kwargs) -> Type[Playlist | User | Episode | Track | Album | Artist | Show]:
        if str(uri) not in self._by_uri.keys():
            # generate element based on type in uri
            to_add = uri.type(uri=uri, cache=self, name=name, **kwargs)
            self._by_uri[str(uri)] = to_add
            self._by_type[uri.type][str(uri)] = to_add

        return self._by_uri[str(uri)]

    # noinspection PyArgumentList
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
            element.load_dict(data=data)
            if element.is_expired():
                raise ElementOutdated()
        except (KeyError, ElementOutdated):
            # maybe cache is outdated
            data = element.make_request(uri=uri, connection=self._connection)
            data["fetched"] = True
            element.load_dict(data=data)

        if not data["fetched"]:
            log.debug("loaded %s from cache", str(uri))

        # cache if needed
        if data["fetched"] and self._cache_dir is not None:
            path = os.path.join(self._cache_dir, str(uri))
            with open(path, "w") as out_file:
                json.dump(element.to_dict(), out_file)
                log.debug("requested and cached %s", str(uri))

    def get_me(self, **kwargs) -> Me:
        if self._me is None:
            self._me = Me(cache=self, **kwargs)
        return self._me

    def get_saved_tracks(self, **kwargs) -> SavedTracks:
        if self._saved_tracks is None:
            to_add = SavedTracks(cache=self, **kwargs)
            self._saved_tracks = to_add
            self._by_uri[str(to_add.uri)] = to_add
            self._by_type[SavedTracks][str(to_add.uri)] = to_add
        return self._saved_tracks

    # noinspection PyTypeChecker
    def load_builtin(self, element: Cacheable, name: str):
        # try to load from cache
        if self._cache_dir is not None:
            path = os.path.join(self._cache_dir, name)
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
            path = os.path.join(self._cache_dir, name)
            with open(path, "w") as out_file:
                json.dump(element.to_dict(), out_file)

    # get cached objects and create them if needed
    def get_track(self, uri: URI, name: str = None, **kwargs) -> Track:
        assert isinstance(uri, URI)
        assert uri.type == Track

        if str(uri) not in self._by_type[Track].keys():
            to_add = Track(uri=uri, cache=self, name=name, **kwargs)
            self._by_type[Track][str(uri)] = to_add
            self._by_uri[str(uri)] = to_add
        return self._by_type[Track][str(uri)]

    def get_playlist(self, uri: URI, name: str = None, **kwargs) -> Playlist:
        assert isinstance(uri, URI)
        assert uri.type == Playlist

        if str(uri) not in self._by_type[Playlist].keys():
            to_add = Playlist(uri=uri, cache=self, name=name, **kwargs)
            self._by_type[Playlist][str(uri)] = to_add
            self._by_uri[str(uri)] = to_add
        return self._by_type[Playlist][str(uri)]

    def get_album(self, uri: URI, name: str = None, **kwargs) -> Album:
        assert isinstance(uri, URI)
        assert uri.type == Album

        if str(uri) not in self._by_type[Album].keys():
            to_add = Album(uri=uri, cache=self, name=name, **kwargs)
            self._by_type[Album][str(uri)] = to_add
            self._by_uri[str(uri)] = to_add
        return self._by_type[Album][str(uri)]

    def get_artist(self, uri: URI, name: str = None, **kwargs) -> Artist:
        assert isinstance(uri, URI)
        assert uri.type == Artist

        if str(uri) not in self._by_type[Artist].keys():
            to_add = Artist(uri=uri, cache=self, name=name, **kwargs)
            self._by_type[Artist][str(uri)] = to_add
            self._by_uri[str(uri)] = to_add
        return self._by_type[Artist][str(uri)]

    def get_user(self, uri: URI, display_name: str = None, **kwargs) -> User:
        assert isinstance(uri, URI)
        assert uri.type == User

        if str(uri) not in self._by_type[User].keys():
            to_add = User(uri=uri, cache=self, display_name=display_name, **kwargs)
            self._by_type[User][str(uri)] = to_add
            self._by_uri[str(uri)] = to_add
        return self._by_type[User][str(uri)]

    def get_episode(self, uri: URI, name: str = None, **kwargs) -> Episode:
        assert isinstance(uri, URI)
        assert uri.type == Episode

        if str(uri) not in self._by_type[Episode].keys():
            to_add = Show(uri=uri, cache=self, name=name, **kwargs)
            self._by_type[Episode][str(uri)] = to_add
            self._by_uri[str(uri)] = to_add
        return self._by_type[Episode][str(uri)]

    def get_show(self, uri: URI, name: str = None, **kwargs) -> Show:
        assert isinstance(uri, URI)
        assert uri.type == Show

        if str(uri) not in self._by_type[Show].keys():
            to_add = Show(uri=uri, cache=self, name=name, **kwargs)
            self._by_type[Show][str(uri)] = to_add
            self._by_uri[str(uri)] = to_add
        return self._by_type[Show][str(uri)]


from .uri import URI
from .user import User
from .playlist import Playlist
from .episode import Episode
from .track import Track
from .artist import Artist
from .album import Album
from .show import Show
from .me import Me, SavedTracks
from .abc import Cacheable
