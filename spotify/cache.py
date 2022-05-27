# resolve circular dependencies
from __future__ import annotations

from .connection import Connection


# noinspection PyUnresolvedReferences
class Cache:
    def __init__(self, connection: Connection, cache_dir: str = None):
        self._cache_dir = cache_dir
        self._connection = connection
        self._playlists = {}
        self._tracks = {}
        self._users = {}

    @property
    def cache_dir(self) -> str:
        return self._cache_dir

    # get cached objects and create them if needed
    def get_track(self, t_id: str, name: str = None) -> Track:
        if t_id not in self._tracks.keys():
            self._tracks[t_id] = Track(t_id=t_id, connection=self._connection, cache=self, name=name)
        return self._tracks[t_id]

    def get_playlist(self, p_id: str, name: str = None) -> Playlist:
        if p_id not in self._tracks.keys():
            self._playlists[p_id] = Playlist(p_id=p_id, connection=self._connection, cache=self, name=name)
        return self._playlists[p_id]

    def get_user(self, u_id: str, display_name: str = None) -> User:
        if u_id not in self._users.keys():
            self._users[u_id] = User(u_id=u_id, connection=self._connection, cache=self, display_name=display_name)
        return self._users[u_id]
