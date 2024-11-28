from __future__ import annotations

import time

from .errors import SpotifyException
from .user import User
from .abc import PlayContext


class SavedTracks(PlayContext):
    """
    Do not create an object of this class yourself. Use :meth:`spotifython.client.saved_tracks` instead.
    """

    def __init__(self, cache: Cache, **kwargs):
        del kwargs

        assert isinstance(cache, Cache)

        self._cache: Cache = cache
        self._name = "Saved Tracks"
        self._items = None
        self._uri: URI | None = None
        self._requested_time: float | None = None

    def to_dict(self, minimal: bool = False) -> dict:
        ret = {"name": self._name, "uri": str(self.uri)}
        if not minimal and self._items is not None:
            ret["tracks"] = {
                "items": [
                    {
                        "added_at": item["added_at"],
                        "track": item["track"].to_dict(minimal=True),
                    }
                    for item in self._items
                ]
            }
            ret["requested_time"] = self._requested_time
        return ret

    @staticmethod
    def make_request(uri: URI | None, connection: Connection) -> dict:
        del uri
        assert isinstance(connection, Connection)

        base = {}
        # get saved tracks
        offset = 0
        limit = 50
        fields = "next,items(added_at,track(uri,name))"
        endpoint = connection.add_parameters_to_endpoint(
            "me/tracks", offset=offset, limit=limit, fields=fields
        )

        if (response := connection.make_request("GET", endpoint)) is not None:
            data = response
        else:
            raise SpotifyException("api request got no data")

        offset += limit
        # check for long data that needs paging
        if data["next"] is not None:
            while True:
                endpoint = connection.add_parameters_to_endpoint(
                    "me/tracks", offset=offset, limit=limit, fields=fields
                )
                offset += limit
                if (response := connection.make_request("GET", endpoint)) is not None:
                    extra_data = response
                else:
                    raise SpotifyException("api request got no data")
                data["items"] += extra_data["items"]

                if extra_data["next"] is None:
                    break
        base["tracks"] = data
        base["requested_time"] = time.time()

        return base

    def load_dict(self, data: dict):
        assert isinstance(data, dict)

        self._items = []
        for item in data["tracks"]["items"]:
            self._items.append(
                {
                    "track": self._cache.get_track(
                        uri=URI(item["track"]["uri"]), name=item["track"]["name"]
                    ),
                    "added_at": item["added_at"],
                }
            )
        self._requested_time = data["requested_time"]

    def is_expired(self) -> bool:
        if self._requested_time is None:
            self._cache.load(uri=self.uri)
        if self._requested_time is not None:
            return time.time() > self._requested_time + (
                3600 * 24 * 7
            )  # one week in unix time
        raise Exception("unreachable")

    @property
    def uri(self) -> URI:
        if self._uri is None:
            self._uri = URI(str(self._cache.get_me().uri) + ":collection")
        return self._uri

    @property
    def items(self) -> list[Track]:
        if self._items is None:
            self._cache.load_builtin(self, "saved_tracks")
        if self._items is not None:
            return [item["track"] for item in self._items]
        raise Exception("unreachable")

    @property
    def images(self) -> list[dict[str, int | str | None]]:
        """
        The saved tracks have no image associated.

        :return: []
        """

        return []


class Me(User):
    """
    Do not create an object of this class yourself. Use :meth:`spotifython.Client.me` instead.
    """

    def __init__(self, cache: Cache, **kwargs):
        del kwargs

        assert isinstance(cache, Cache)
        self._uri: URI | None = None
        self._cache: Cache = cache
        self._playlists: list[Playlist] | None = None
        self._albums: list[Album] | None = None
        self._requested_time: float | None = None

    @staticmethod
    def make_request(uri: URI | None, connection: Connection) -> dict:
        del uri
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "me", fields="display_name,uri"
        )
        if (response := connection.make_request("GET", endpoint)) is not None:
            base = response
        else:
            raise SpotifyException("api request got no data")

        # get saved albums
        offset = 0
        limit = 50
        endpoint = connection.add_parameters_to_endpoint(
            "me/albums", offset=offset, limit=limit, fields="items(album(uri,name))"
        )

        if (response := connection.make_request("GET", endpoint)) is not None:
            data = response
        else:
            raise SpotifyException("api request got no data")

        # check for long data that needs paging
        if "next" in data and data["next"] is not None:
            while True:
                endpoint = connection.add_parameters_to_endpoint(
                    "me/albums",
                    offset=offset,
                    limit=limit,
                    fields="items(album(uri,name))",
                )
                offset += limit
                if (response := connection.make_request("GET", endpoint)) is not None:
                    extra_data = response
                else:
                    raise SpotifyException("api request got no data")
                data["items"] += extra_data["items"]

                if "next" in extra_data and extra_data["next"] is None:
                    break
        base["albums"] = data

        # get saved playlists
        offset = 0
        limit = 50
        endpoint = connection.add_parameters_to_endpoint(
            "me/playlists",
            offset=offset,
            limit=limit,
            fields="items(uri,name,snapshot_id)",
        )

        if (response := connection.make_request("GET", endpoint)) is not None:
            data = response
        else:
            raise SpotifyException("api request got no data")

        # check for long data that needs paging
        if "next" in data and data["next"] is not None:
            while True:
                endpoint = connection.add_parameters_to_endpoint(
                    "me/playlists",
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

                if "next" in extra_data and extra_data["next"] is None:
                    break
        base["playlists"] = data

        base["requested_time"] = time.time()

        return base

    def load_dict(self, data: dict):
        assert isinstance(data, dict)

        self._uri = URI(data["uri"])
        self._name = data["display_name"]

        self._albums = []
        for album in data["albums"]["items"]:
            if album == {}:
                continue
            self._albums.append(
                self._cache.get_album(
                    uri=URI(album["album"]["uri"]),
                    name=album["album"]["name"],
                )
            )
        self._playlists = []
        for playlist in data["playlists"]["items"]:
            if playlist == {}:
                continue
            self._playlists.append(
                self._cache.get_playlist(
                    uri=URI(playlist["uri"]),
                    name=playlist["name"],
                    snapshot_id=playlist["snapshot_id"],
                )
            )
        self._requested_time = data["requested_time"]

    def to_dict(self, minimal: bool = False) -> dict:
        ret = super().to_dict(minimal=minimal)

        if not minimal and self._albums is not None:
            ret["albums"] = {
                "items": [
                    {"album": album.to_dict(minimal=True)} for album in self._albums
                ]
            }
        return ret

    def is_expired(self) -> bool:
        if self._requested_time is None:
            self._cache.load(uri=self.uri)
        if self._requested_time is not None:
            return time.time() > self._requested_time + (
                3600 * 24
            )  # one day in unix time
        raise Exception("unreachable")

    @property
    def uri(self) -> URI:
        if self._uri is None:
            self._cache.load_builtin(self, "me")
        if self._uri is not None:
            return self._uri
        raise Exception("unreachable")

    @property
    def display_name(self) -> str:
        if self._name is None:
            self._cache.load_builtin(self, "me")
        if self._name is not None:
            return self._name
        raise Exception("unreachable")

    @property
    def playlists(self) -> list[Playlist]:
        if self._playlists is None:
            self._cache.load_builtin(self, "me")
        if self._playlists is not None:
            return self._playlists.copy()
        raise Exception("unreachable")

    @property
    def albums(self) -> list[Album]:
        if self._albums is None:
            self._cache.load_builtin(self, "me")
        if self._albums is not None:
            return self._albums.copy()
        raise Exception("unreachable")

    @property
    def name(self) -> str:
        if self._name is None:
            self._cache.load_builtin(self, "me")
        if self._name is not None:
            return self._name
        raise Exception("unreachable")

    @property
    def saved_tracks(self) -> SavedTracks:
        return self._cache.get_saved_tracks()


from .cache import Cache
from .uri import URI
from .connection import Connection
from .track import Track
from .playlist import Playlist
from .album import Album
