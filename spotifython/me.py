from __future__ import annotations

import time

from .user import User
from .abc import PlayContext


class SavedTracks(PlayContext):
    """
    Do not create an object of this class yourself. Use :meth:`spotifython.client.saved_tracks` instead.
    """

    # noinspection PyMissingConstructor,PyUnusedLocal
    def __init__(self, cache: Cache, **kwargs):
        assert isinstance(cache, Cache)

        self._cache = cache
        self._name = "Saved Tracks"
        self._items = None
        self._uri = None
        self._requested_time = None

    def to_dict(self, short: bool = False, minimal: bool = False) -> dict:
        ret = {
            "name": self._name,
            "uri": str(self.uri)
        }
        if not minimal and not short:
            ret["tracks"] = {
                "items": [
                    {
                        "added_at": item["added_at"],
                        "track": item["track"].to_dict(minimal=True)
                    }
                    for item in self._items
                ]
            }
            ret["requested_time"] = self._requested_time
        return ret

    @staticmethod
    def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(connection, Connection)

        base = {}
        # get saved tracks
        offset = 0
        limit = 50
        endpoint = connection.add_parameters_to_endpoint(
            "me/tracks",
            offset=offset,
            limit=limit,
            fields="items(uri,name)"
        )

        data = connection.make_request("GET", endpoint)
        # check for long data that needs paging
        if data["next"] is not None:
            while True:
                endpoint = connection.add_parameters_to_endpoint(
                    "me/tracks",
                    offset=offset,
                    limit=limit,
                    fields="items(uri,name)"
                )
                offset += limit
                extra_data = connection.make_request("GET", endpoint)
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
            self._items.append({
                "track": self._cache.get_track(uri=URI(item["track"]["uri"]), name=item["track"]["name"]),
                "added_at": item["added_at"]
            })
        self._requested_time = data["requested_time"]

    def is_expired(self) -> bool:
        if self._requested_time is None:
            self._cache.load(uri=self._uri)
        return time.time() > self._requested_time + 514800  # one week in unix time

    @property
    def uri(self) -> URI:
        if self._uri is None:
            self._uri = URI(str(self._cache.get_me().uri) + ":collection")
        return self._uri

    @property
    def items(self) -> list[Track]:
        if self._items is None:
            self._cache.load_builtin(self, "saved_tracks")
        return [item["track"] for item in self._items]

    @property
    def images(self) -> list[dict[str, (int, str, None)]]:
        """
        The saved tracks have no image associated.

        :return: []
        """

        return []


class Me(User):
    """
    Do not create an object of this class yourself. Use :meth:`spotifython.Client.me` instead.
    """

    # noinspection PyMissingConstructor,PyUnusedLocal
    def __init__(self, cache: Cache, **kwargs):
        assert isinstance(cache, Cache)
        self._uri = None
        self._cache = cache
        self._playlists = None
        self._requested_time = None

    # noinspection PyUnusedLocal
    @staticmethod
    def make_request(uri: (URI, None), connection: Connection) -> dict:
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "me",
            fields="display_name,uri"
        )
        base = connection.make_request("GET", endpoint)

        # get saved playlists
        offset = 0
        limit = 50
        endpoint = connection.add_parameters_to_endpoint(
            "me/playlists",
            offset=offset,
            limit=limit,
            fields="items(uri,name,snapshot_id)"
        )

        data = connection.make_request("GET", endpoint)
        # check for long data that needs paging
        if data["next"] is not None:
            while True:
                endpoint = connection.add_parameters_to_endpoint(
                    "me/playlists",
                    offset=offset,
                    limit=limit,
                    fields="items(uri,name,snapshot_id)"
                )
                offset += limit
                extra_data = connection.make_request("GET", endpoint)
                data["items"] += extra_data["items"]

                if extra_data["next"] is None:
                    break
        base["playlists"] = data

        base["requested_time"] = time.time()

        return base

    def load_dict(self, data: dict):
        assert isinstance(data, dict)

        self._uri = URI(data["uri"])
        self._name = data["display_name"]

        self._playlists = []
        for playlist in data["playlists"]["items"]:
            self._playlists.append(self._cache.get_playlist(
                uri=URI(playlist["uri"]),
                name=playlist["name"],
                snapshot_id=playlist["snapshot_id"]
            ))
        self._requested_time = data["requested_time"]

    def to_dict(self, short: bool = False, minimal: bool = False) -> dict:
        ret = super().to_dict(short=short, minimal=minimal)
        return ret

    def is_expired(self) -> bool:
        if self._requested_time is None:
            self._cache.load(uri=self._uri)
        return time.time() > self._requested_time + 514800  # one week in unix time

    @property
    def uri(self) -> str:
        if self._uri is None:
            self._cache.load_builtin(self, "me")
        return self._uri

    @property
    def display_name(self) -> str:
        if self._name is None:
            self._cache.load_builtin(self, "me")
        return self._name

    @property
    def playlists(self) -> list[Playlist]:
        if self._playlists is None:
            self._cache.load_builtin(self, "me")
        return self._playlists.copy()

    @property
    def name(self) -> str:
        if self._name is None:
            self._cache.load_builtin(self, "me")
        return self._name

    @property
    def saved_tracks(self) -> SavedTracks:
        return self._cache.get_saved_tracks()


from .cache import Cache
from .uri import URI
from .connection import Connection
from .track import Track
from .playlist import Playlist
