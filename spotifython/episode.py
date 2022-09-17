from __future__ import annotations

from .abc import Playable
from .uri import URI
from .cache import Cache
from .connection import Connection


# noinspection PyProtectedMember
class Episode(Playable):
    """
    Do not create an object of this class yourself. Use :meth:`spotifython.Client.get_episode` instead.
    """
    def __init__(self, uri: URI, cache: Cache, name: str = None, **kwargs):
        super().__init__(uri=uri, cache=cache, name=name, **kwargs)

        self._images = None
        self._show = None

    def to_dict(self, short: bool = False, minimal: bool = False) -> dict:
        ret = {"uri": str(self._uri)}
        if self._name is not None: ret["name"] = self._name

        if not minimal:
            if self._show is None:
                self._cache.load(self.uri)

            ret["name"] = self._name
            ret["images"] = self._images
            ret["show"] = self._show.to_dict(minimal=True)
        return ret

    @staticmethod
    def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)

        endpoint = connection.add_parameters_to_endpoint(
            "albums/{id}".format(id=uri.id),
            fields="uri,name,images,show(uri,name)"
        )
        return connection.make_request("GET", endpoint)

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._name = data["name"]
        self._images = data["images"]
        self._show = self._cache.get_show(uri=URI(data["show"]["uri"]), name=data["show"]["name"])

    def is_expired(self) -> bool:
        return False

    @property
    def images(self) -> list[dict[str, (str, int, None)]]:
        """
        get list of the image registered with spotify in different sizes

        :return: [{'height': (int | None), 'width': (int | None), 'url': str}]
        """
        if self._images is None:
            self._cache.load(uri=self._uri)
        return self._images.copy()

    @property
    def show(self) -> Show:
        if self._show is None:
            self._cache.load(uri=self._uri)
        return self._show

    @staticmethod
    def save(episodes: list[Episode]):
        """
        add the given albums to saved albums of the current user
        """
        assert isinstance(episodes, list)
        assert len(episodes) > 0

        if len(episodes) > 50:
            Episode.save(episodes[50:])
            episodes = episodes[:50]

        ids = [track.uri.id for track in episodes]

        connection = episodes[0]._cache._connection
        endpoint = connection.add_parameters_to_endpoint(
            "me/albums",
            ids=",".join(ids),
        )
        connection.make_request("PUT", endpoint)

    @staticmethod
    def unsave(episodes: list[Episode]):
        """
        remove the given albums from saved albums of the current user. fails silently if the episode is not saved
        """
        assert isinstance(episodes, list)
        assert len(episodes) > 0

        if len(episodes) > 50:
            Episode.unsave(episodes[50:])
            episodes = episodes[:50]

        ids = [track.uri.id for track in episodes]

        connection = episodes[0]._cache._connection
        endpoint = connection.add_parameters_to_endpoint(
            "me/albums",
            ids=",".join(ids),
        )
        connection.make_request("DELETE", endpoint)


from .show import Show
