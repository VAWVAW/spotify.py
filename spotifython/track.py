from __future__ import annotations

from spotifython.errors import SpotifyException

from .connection import Connection
from .cache import Cache
from .uri import URI
from .abc import Playable


class Track(Playable):
    """
    Do not create an object of this class yourself. Use :meth:`spotifython.Client.get_track` instead.
    """

    def __init__(self, uri: URI, cache: Cache, name: str | None = None, **kwargs):
        super().__init__(uri=uri, cache=cache, name=name, **kwargs)

        self._album: Album | None = None
        self._artists: list[Artist] | None = None

    def to_dict(self, minimal: bool = False) -> dict:
        ret = {"uri": str(self._uri)}
        if self._name is not None:
            ret["name"] = self._name

        if not minimal:
            if self._artists is None:
                self._cache.load(self.uri)

            if self._name is not None:
                ret["name"] = self._name
            if self._album is not None:
                ret["album"] = self._album.to_dict(minimal=True)
            if self._artists is not None:
                ret["artists"] = [
                    artist.to_dict(minimal=True) for artist in self._artists
                ]
        return ret

    @staticmethod
    def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "tracks/{id}".format(id=uri.id),
            fields="uri,name,album(uri,name),artists(uri,name)",
        )
        response = connection.make_request("GET", endpoint)
        if response is not None:
            return response
        raise SpotifyException("api request got no data")

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._name = data["name"]
        self._album = self._cache.get_album(
            uri=URI(data["album"]["uri"]), name=data["album"]["name"]
        )
        self._artists = []

        for artist in data["artists"]:
            self._artists.append(
                self._cache.get_artist(uri=URI(artist["uri"]), name=artist["name"])
            )

    def is_expired(self) -> bool:
        return False

    @property
    def album(self) -> Album:
        if self._album is None:
            self._cache.load(uri=self._uri)
        if self._album is not None:
            return self._album
        raise Exception("unreachable")

    @property
    def artists(self) -> list[Artist]:
        if self._artists is None:
            self._cache.load(uri=self._uri)
        if self._artists is not None:
            return self._artists.copy()
        raise Exception("unreachable")

    @property
    def images(self) -> list[dict[str, int | str | None]]:
        """
        get list of the image registered with spotify in different sizes

        :return: [{'height': (int | None), 'width': (int | None), 'url': str}]
        """
        return self.album.images

    @staticmethod
    def save(tacks: list[Track]):
        """
        add the given tracks to saved tracks of the current user
        """
        assert isinstance(tacks, list)
        assert len(tacks) > 0

        if len(tacks) > 50:
            Track.save(tacks[50:])
            tacks = tacks[:50]

        ids = [track.uri.id for track in tacks]

        connection = tacks[0]._cache._connection
        endpoint = connection.add_parameters_to_endpoint(
            "me/tracks",
            ids=",".join(ids),
        )
        connection.make_request("PUT", endpoint)

    @staticmethod
    def unsave(tacks: list[Track]):
        """
        remove the given tracks from saved tracks of the current user. fails silently if the track is not saved
        """
        assert isinstance(tacks, list)
        assert len(tacks) > 0

        if len(tacks) > 50:
            Track.unsave(tacks[50:])
            tacks = tacks[:50]

        ids = [track.uri.id for track in tacks]

        connection = tacks[0]._cache._connection
        endpoint = connection.add_parameters_to_endpoint(
            "me/tracks",
            ids=",".join(ids),
        )
        connection.make_request("DELETE", endpoint)


from .album import Album
from .artist import Artist
