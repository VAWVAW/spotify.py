from __future__ import annotations

import time

from .errors import SpotifyException
from .abc import Cacheable


class User(Cacheable):
    """
    Do not create an object of this class yourself. Use :meth:`spotifython.Client.get_user` instead.
    """

    def __init__(
        self, uri: URI, cache: Cache, display_name: str | None = None, **kwargs
    ):
        super().__init__(uri=uri, cache=cache, name=display_name, **kwargs)
        self._playlists: list[Playlist] | None = None
        self._requested_time: float | None = None

    def to_dict(self, minimal: bool = False) -> dict:
        ret = {"uri": str(self.uri)}
        if self._name is not None:
            ret["display_name"] = self._name

        if not minimal:
            if self._playlists is None:
                self._cache.load(self.uri)

            if self._name is not None:
                ret["display_name"] = self._name

            if self._playlists is not None:
                ret["playlists"] = {
                    "items": [
                        playlist.to_dict(minimal=True) for playlist in self._playlists
                    ]
                }

        if self._requested_time is not None:
            ret["requested_time"] = self._requested_time
        return ret

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._name = data["display_name"]

        self._playlists = []
        for playlist in data["playlists"]["items"]:
            self._playlists.append(
                self._cache.get_playlist(
                    uri=URI(playlist["uri"]),
                    name=playlist["name"],
                    snapshot_id=playlist["snapshot_id"],
                )
            )
        self._requested_time = data["requested_time"]

    @staticmethod
    def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "users/{user_id}".format(user_id=uri.id), fields="display_name,uri"
        )
        if (response := connection.make_request("GET", endpoint)) is not None:
            base = response
        else:
            raise SpotifyException("api request got no data")

        # get playlists
        offset = 0
        limit = 50
        endpoint = connection.add_parameters_to_endpoint(
            "users/{userid}/playlists".format(userid=uri.id),
            offset=offset,
            limit=limit,
            fields="items(uri,name,snapshot_id)",
        )

        if (response := connection.make_request("GET", endpoint)) is not None:
            data = response
        else:
            raise SpotifyException("api request got no data")

        # check for long data that needs paging
        if data["next"] is not None:
            while True:
                endpoint = connection.add_parameters_to_endpoint(
                    "users/{userid}/playlists".format(userid=uri.id),
                    offset=offset,
                    limit=limit,
                    fields="items(uri,name,snapshot_id)",
                )
                offset += limit
                if (response := connection.make_request("GET", endpoint)) is not None:
                    extra_data = response
                else:
                    raise SpotifyException("api request got no data")
                data["items"] += extra_data["items"]

                if extra_data["next"] is None:
                    break
        base["playlists"] = data
        base["requested_time"] = time.time()

        return base

    def is_expired(self) -> bool:
        if self._requested_time is None:
            self._cache.load(uri=self._uri)
        if self._requested_time is not None:
            return time.time() > self._requested_time + (
                3600 * 24 * 7
            )  # one week in unix time
        raise Exception("unreachable")

    @property
    def display_name(self) -> str:
        """
        Same as name
        """

        if self._name is None:
            self._cache.load(self.uri)
        if self._name is not None:
            return self._name
        raise Exception("unreachable")

    @property
    def playlists(self) -> list[Playlist]:
        if self._playlists is None:
            self._cache.load(self.uri)
        if self._playlists is not None:
            return self._playlists.copy()
        raise Exception("unreachable")


from .playlist import Playlist
from .cache import Cache
from .uri import URI
from .connection import Connection
