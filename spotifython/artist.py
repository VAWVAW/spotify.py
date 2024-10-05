import time

from .errors import SpotifyException
from .abc import Cacheable
from .cache import Cache
from .connection import Connection
from .uri import URI
from .track import Track


class Artist(Cacheable):
    """
    Do not create an object of this class yourself. Use :meth:`spotifython.Client.get_artist` instead.
    """

    def __init__(self, uri: URI, cache: Cache, name: str | None = None, **kwargs):
        super().__init__(uri=uri, cache=cache, name=name, **kwargs)

        self._tracks: list[Track] | None = None
        self._requested_time: float | None = None

    def to_dict(self, minimal: bool = False) -> dict:

        ret = {"uri": str(self._uri)}
        if self._name is not None:
            ret["name"] = self._name

        if not minimal:
            if self._name is None:
                self._cache.load(self.uri)

            if self._name is not None:
                ret["name"] = self._name

            if self._tracks is not None:
                ret["tracks"] = [track.to_dict(minimal=True) for track in self._tracks]

            if self._requested_time is not None:
                ret["requested_time"] = self._requested_time
        return ret

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._name = data["name"]
        self._requested_time = data["requested_time"]
        self._tracks = [
            self._cache.get_track(uri=URI(track["uri"]), name=track.get("name"))
            for track in data["tracks"]
        ]

    @staticmethod
    def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "artists/{artist_id}".format(artist_id=uri.id), fields="name,uri"
        )
        if (response := connection.make_request("GET", endpoint)) is not None:
            data = response
        else:
            raise SpotifyException("api request got no data")

        endpoint = connection.add_parameters_to_endpoint(
            "artists/{artist_id}/top-tracks".format(artist_id=uri.id),
            fields="tracks(uri,name)",
        )
        if (response := connection.make_request("GET", endpoint)) is not None:
            extra_data = response
        else:
            raise SpotifyException("api request got no data")
        data["tracks"] = extra_data["tracks"]

        data["requested_time"] = time.time()
        return data

    def is_expired(self) -> bool:
        if self._requested_time is None:
            self._cache.load(uri=self._uri)
        if self._requested_time is not None:
            return time.time() > self._requested_time + (
                3600 * 24 * 7
            )  # one week in unix time
        raise Exception("unreachable")

    @property
    def top_tracks(self) -> list[Track]:
        """
        get list of the artists top played tracks

        """
        if self._tracks is None:
            self._cache.load(uri=self._uri)
        if self._tracks is not None:
            return self._tracks.copy()
        raise Exception("unreachable")
