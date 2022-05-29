# resolve circular dependencies
from __future__ import annotations

import json
import os.path

from .connection import Connection
from .uri import URI
from .errors import ElementOutdated
from .scope import Scope


class Cache:
    def __init__(self, connection: Connection, cache_dir: str = None):
        self._cache_dir = cache_dir
        self._connection = connection
        self._by_uri = {}
        self._by_type = {
            "playlist": {},
            "episode": {},
            "track": {},
            "user": {}
        }

        self._datatypes = {
            "playlist": Playlist,
            "episode": Episode,
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
        except (KeyError, ElementOutdated):
            # maybe cache is outdated
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

    def load_token(self, client_id: str = None, client_secret: str = None, refresh_token: str = None, scope: Scope = Scope(), show_dialog: bool = False, token: str = None, expires: int = 0):
        if self._cache_dir is not None:
            try:
                with open(os.path.join(self._cache_dir, "token"), "r") as in_file:
                    cached = json.load(in_file)

                # load cached data if needed
                if client_id is None and cached["client_id"] is not None:
                    client_id = cached["client_id"]
                if client_secret is None and cached["client_secret"] is not None:
                    client_secret = cached["client_secret"]
                if refresh_token is None and cached["refresh_token"] is not None:
                    refresh_token = cached["refresh_token"]
                if token is None and cached["token"] is not None:
                    token = cached["token"]
                    expires = cached["expires"]

                if not scope.is_equal(cached["scope"]):
                    refresh_token = None

            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                # don't use cached data and recache
                pass

        self._connection.set_token_data(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token, scope=scope, show_dialog=show_dialog, token=token, expires=expires)

    def close(self):
        if self._cache_dir is None:
            return
        with open(os.path.join(self._cache_dir, "token"), "w") as out_file:
            json.dump(self._connection.dump_token_data(), out_file)


from .playlist import Playlist
from .episode import Episode
from .user import User
from .track import Track
from .abc import Cacheable
