from __future__ import annotations

import time
from .errors import SpotifyException
from .abc import PlayContext
from .uri import URI
from .cache import Cache
from .connection import Connection
from .episode import Episode


class Show(PlayContext):
    """
    Do not create an object of this class yourself. Use :meth:`spotifython.Client.get_show` instead.
    """

    def __init__(self, uri: URI, cache: Cache, name: str | None = None, **kwargs):
        super().__init__(uri=uri, cache=cache, name=name, **kwargs)

        self._items: list[Episode] | None = None
        self._images: list[dict[str, str | int | None]] | None = None
        self._description: str | None = None
        self._requested_time: float | None = None

    def to_dict(self, minimal: bool = False) -> dict:
        ret = {"uri": str(self._uri)}
        if self._name is not None:
            ret["name"] = self._name

        if not minimal:
            if self._items is None:
                self._cache.load(self.uri)

            if self._name is not None:
                ret["name"] = self._name
            if self._description is not None:
                ret["description"] = self._description
            if self._images is not None:
                ret["images"] = self._images
            if self._requested_time is not None:
                ret["requested_time"] = self._requested_time

            if self._items is not None:
                ret["albums"] = {
                    "items": [item.to_dict(minimal=True) for item in self._items]
                }
        return ret

    @staticmethod
    def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)
        assert uri.type == Show

        offset = 0
        limit = 50
        endpoint = connection.add_parameters_to_endpoint(
            "albums/{id}".format(id=uri.id), offset=offset, limit=limit
        )

        if (response := connection.make_request("GET", endpoint)) is not None:
            data = response
        else:
            raise SpotifyException("api request got no data")

        # check for long data that needs paging
        if data["albums"]["next"] is not None:
            while True:
                offset += limit
                endpoint = connection.add_parameters_to_endpoint(
                    "albums/{id}/albums".format(id=uri.id), offset=offset, limit=limit
                )
                if (response := connection.make_request("GET", endpoint)) is not None:
                    extra_data = response
                else:
                    raise SpotifyException("api request got no data")
                data["albums"]["items"] += extra_data["items"]

                if extra_data["next"] is None:
                    break

        data["requested_time"] = time.time()

        return data

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._requested_time = data["requested_time"]
        self._name = data["name"]
        self._images = data["images"]
        self._description = data["description"]
        self._items = []

        for episode in data["albums"]["items"]:
            if episode is None:
                continue
            self._items.append(
                self._cache.get_episode(uri=URI(episode["uri"]), name=episode["name"])
            )

    def is_expired(self) -> bool:
        if self._requested_time is None:
            self._cache.load(uri=self._uri)
        if self._requested_time is not None:
            return time.time() > self._requested_time + (
                3600 * 24 * 7
            )  # one week in unix time
        raise Exception("unreachable")

    @property
    def episodes(self) -> list[Episode]:
        if self._items is None:
            self._cache.load(uri=self._uri)
        if self._items is not None:
            return self._items.copy()
        raise Exception("unreachable")

    @property
    def items(self) -> list[Episode]:
        if self._items is None:
            self._cache.load(uri=self._uri)
        if self._items is not None:
            return self._items.copy()
        raise Exception("unreachable")

    @property
    def images(self) -> list[dict[str, str | int | None]]:
        """
        get list of the image registered with spotify in different sizes

        :return: [{'height': (int | None), 'width': (int | None), 'url': str}]
        """
        if self._images is None:
            self._cache.load(uri=self._uri)
        if self._images is not None:
            return self._images.copy()
        raise Exception("unreachable")

    @property
    def description(self) -> str:
        if self._description is None:
            self._cache.load(uri=self._uri)
        if self._description is not None:
            return self._description
        raise Exception("unreachable")

    @staticmethod
    def save(shows: list[Show]):
        """
        add the given albums to saved albums of the current user
        """
        assert isinstance(shows, list)
        assert len(shows) > 0

        if len(shows) > 50:
            Show.save(shows[50:])
            shows = shows[:50]

        ids = [track.uri.id for track in shows]

        connection = shows[0]._cache._connection
        endpoint = connection.add_parameters_to_endpoint(
            "me/albums",
            ids=",".join(ids),
        )
        connection.make_request("PUT", endpoint)

    @staticmethod
    def unsave(shows: list[Show]):
        """
        remove the given albums from saved albums of the current user. fails silently if the show is not saved
        """
        assert isinstance(shows, list)
        assert len(shows) > 0

        if len(shows) > 50:
            Show.unsave(shows[50:])
            shows = shows[:50]

        ids = [track.uri.id for track in shows]

        connection = shows[0]._cache._connection
        endpoint = connection.add_parameters_to_endpoint(
            "me/albums",
            ids=",".join(ids),
        )
        connection.make_request("DELETE", endpoint)
