import time

from .errors import SpotifyException
from .abc import Cacheable
from .cache import Cache
from .connection import Connection
from .uri import URI


class Artist(Cacheable):
    """
    Do not create an object of this class yourself. Use :meth:`spotifython.Client.get_artist` instead.
    """

    def __init__(self, uri: URI, cache: Cache, name: str | None = None, **kwargs):
        super().__init__(uri=uri, cache=cache, name=name, **kwargs)
        self._requested_time: float | None = None

    def to_dict(self, short: bool = False, minimal: bool = False) -> dict:
        del short

        ret = {"uri": str(self._uri)}
        if self._name is not None:
            ret["name"] = self._name

        if not minimal:
            if self._name is None:
                self._cache.load(self.uri)

            if self._name is not None:
                ret["name"] = self._name
            if self._requested_time is not None:
                ret["requested_time"] = self._requested_time
        return ret

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._name = data["name"]
        self._requested_time = data["requested_time"]

    @staticmethod
    def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "artists/{artist_id}".format(artist_id=uri.id), fields="name,uri"
        )
        response = connection.make_request("GET", endpoint)
        if response is not None:
            response["requested_time"] = time.time()
            return response
        raise SpotifyException("api request got no data")

    def is_expired(self) -> bool:
        if self._requested_time is None:
            self._cache.load(uri=self._uri)
        if self._requested_time is not None:
            return time.time() > self._requested_time + (
                3600 * 24 * 7
            )  # one week in unix time
        raise Exception("unreachable")
