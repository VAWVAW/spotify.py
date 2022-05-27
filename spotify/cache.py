# resolve circular dependencies
from __future__ import annotations

from .connection import Connection


# noinspection PyUnresolvedReferences
class Cache:
    def __init__(self, connection: Connection, cache_dir: str = None):
        self._cache_dir = cache_dir
        self._connection = connection
        self._data = {}

    @property
    def cache_dir(self) -> str:
        return self._cache_dir

    # get cached objects and create them if needed
    def get_track(self, uri: URI, name: str = None) -> Track:
        if uri not in self._tracks.keys():
            self._tracks[uri] = Track(uri=uri, connection=self._connection, cache=self, name=name)
        return self._tracks[uri]

    def get_playlist(self, uri: URI, name: str = None) -> Playlist:
        if uri not in self._tracks.keys():
            self._playlists[uri] = Playlist(uri=uri, connection=self._connection, cache=self, name=name)
        return self._playlists[uri]

    def get_user(self, uri: URI, display_name: str = None) -> User:
        if uri not in self._users.keys():
            self._users[uri] = User(uri=uri, connection=self._connection, cache=self, display_name=display_name)
        return self._users[uri]


from .playlist import Playlist
from .user import User
from .track import Track
