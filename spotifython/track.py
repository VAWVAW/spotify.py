from __future__ import annotations

from .connection import Connection
from .cache import Cache
from .uri import URI
from .abc import Playable
from .artist import Artist


# noinspection PyProtectedMember
class Track(Playable):
    """
    Do not create an object of this class yourself. Use :meth:`spotifython.Client.get_track` instead.
    """

    def __init__(self, uri: URI, cache: Cache, name: str = None, **kwargs):
        super().__init__(uri=uri, cache=cache, name=name, **kwargs)

        self._album = None
        self._artists = None

    def to_dict(self, short: bool = False, minimal: bool = False) -> dict:
        ret = {"uri": str(self._uri)}
        if self._name is not None: ret["name"] = self._name

        if not minimal:
            if self._artists is None:
                self._cache.load(self.uri)

            ret["name"] = self._name
            ret["album"] = self._album.to_dict(minimal=True)
            ret["artists"] = [artist.to_dict(minimal=True) for artist in self._artists]
        return ret

    @staticmethod
    def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "tracks/{id}".format(id=uri.id),
            fields="uri,name,album(uri,name),artists(uri,name)",
        )
        return connection.make_request("GET", endpoint)

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._name = data["name"]
        self._album = self._cache.get_album(uri=URI(data["album"]["uri"]), name=data["album"]["name"])
        self._artists = []

        for artist in data["artists"]:
            self._artists.append(self._cache.get_artist(uri=URI(artist["uri"]), name=artist["name"]))

    def is_expired(self) -> bool:
        return False

    @property
    def album(self) -> Album:
        if self._album is None:
            self._cache.load(uri=self._uri)
        return self._album

    @property
    def artists(self) -> list[Artist]:
        if self._artists is None:
            self._cache.load(uri=self._uri)
        return self._artists.copy()

    @property
    def images(self) -> list[dict[str, (int, str, None)]]:
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
