from __future__ import annotations

from .abc import Cacheable


class User(Cacheable):
    """
    Do not create an object of this class yourself. Use :meth:`spotifython.Client.get_artist` instead.
    """

    def __init__(self, uri: URI, cache: Cache, display_name: str = None, **kwargs):
        super().__init__(uri=uri, cache=cache, name=display_name, **kwargs)
        self._playlists = None

    def to_dict(self, short: bool = False, minimal: bool = False) -> dict:
        ret = {"uri": str(self._uri)}
        if self._name is not None: ret["display_name"] = self._name

        if not minimal:
            if self._playlists is None:
                self._cache.load(self.uri)

            ret["display_name"] = self._name

            if not short:
                ret["playlists"] = {
                    "items": [playlist.to_dict(minimal=True) for playlist in self._playlists]
                }

        return ret

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._name = data["display_name"]

        self._playlists = []
        for playlist in data["playlists"]["items"]:
            self._playlists.append(self._cache.get_playlist(
                uri=URI(playlist["uri"]),
                name=playlist["name"],
                snapshot_id=playlist["snapshot_id"]
            ))

    @staticmethod
    def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "users/{user_id}".format(user_id=uri.id),
            fields="display_name,uri"
        )
        base = connection.make_request("GET", endpoint)

        # get playlists
        offset = 0
        limit = 50
        endpoint = connection.add_parameters_to_endpoint(
            "users/{userid}/playlists".format(userid=uri.id),
            offset=offset,
            limit=limit,
            fields="items(uri,name,snapshot_id)"
        )

        data = connection.make_request("GET", endpoint)
        # check for long data that needs paging
        if data["next"] is not None:
            while True:
                endpoint = connection.add_parameters_to_endpoint(
                    "users/{userid}/playlists".format(userid=uri.id),
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

        return base

    @property
    def display_name(self) -> str:
        if self._name is None:
            self._cache.load(self.uri)
        return self._name

    @property
    def playlists(self) -> list[Playlist]:
        if self._playlists is None:
            self._cache.load(self.uri)
        return self._playlists.copy()


class Me(User):
    # noinspection PyMissingConstructor,PyUnusedLocal
    def __init__(self, cache: Cache, **kwargs):
        assert isinstance(cache, Cache)
        self._uri = None
        self._cache = cache
        self._playlists = None
        self._tracks = None

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
        self._tracks = []
        for track in data["tracks"]["items"]:
            self._tracks.append({
                "track": self._cache.get_track(uri=URI(track["track"]["uri"]), name=track["track"]["name"]),
                "added_at": track["added_at"]
            })

    def to_dict(self, short: bool = False, minimal: bool = False) -> dict:
        ret = super().to_dict(short=short, minimal=minimal)
        if not short:
            ret["tracks"] = {
                "items": [
                    {
                        "added_at": item["added_at"],
                        "track": item["track"].to_dict(minimal=True)
                    }
                    for item in self._tracks
                ]
            }
        return ret

    @property
    def uri(self) -> str:
        if self._uri is None:
            self._cache.load_me()
        return self._uri

    @property
    def display_name(self) -> str:
        if self._name is None:
            self._cache.load_me()
        return self._name

    @property
    def playlists(self) -> list[Playlist]:
        if self._playlists is None:
            self._cache.load_me()
        return self._playlists.copy()

    @property
    def name(self) -> str:
        if self._name is None:
            self._cache.load_me()
        return self._name

    @property
    def tracks(self) -> list[dict[str, (str | Track)]]:
        if self._tracks is None:
            self._cache.load_me()
        return self._tracks.copy()


from .playlist import Playlist
from .cache import Cache
from .uri import URI
from .connection import Connection
from .track import Track
