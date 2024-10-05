from __future__ import annotations

import time

from .connection import Connection
from .user import User
from .cache import Cache
from .uri import URI
from .abc import PlayContext, Playable
from .errors import ElementOutdated, SpotifyException


class Playlist(PlayContext):
    """
    Do not create an object of this class yourself. Use :meth:`spotifython.Client.get_playlist` instead.
    """

    def __init__(
        self,
        uri: URI,
        cache: Cache,
        name: str | None = None,
        check_outdated: bool = True,
        **kwargs,
    ):
        super().__init__(uri=uri, cache=cache, name=name, **kwargs)

        self._snapshot_id: str | None = kwargs.get("snapshot_id")
        self._check_outdated: bool = check_outdated

        self._description: str | None = None
        self._owner: User | None = None
        self._public: bool | None = None
        self._items: list[dict[str, Track | Episode]] | None = None
        self._images: list[dict[str, str | int | None]] | None = None
        self._requested_time: float | None = None

    def to_dict(self, minimal: bool = False) -> dict:
        ret = {"uri": str(self._uri)}
        if self._name is not None:
            ret["name"] = self._name
        if self._snapshot_id is not None:
            ret["snapshot_id"] = self._snapshot_id

        if not minimal:
            if self._items is None:
                self._cache.load(self.uri)

            if self._name is not None:
                ret["name"] = self._name
            if self._snapshot_id is not None:
                ret["snapshot_id"] = self._snapshot_id

            if self._images is not None:
                ret["images"] = self._images
            if self._public is not None:
                ret["public"] = self._public
            if self._description is not None:
                ret["description"] = self._description
            if self._owner is not None:
                ret["owner"] = self._owner.to_dict(minimal=True)
            if self._requested_time is not None:
                ret["requested_time"] = self._requested_time

            if self._items is not None:
                ret["tracks"] = {
                    "items": [
                        {
                            "added_at": item["added_at"],
                            "track": item["track"].to_dict(minimal=True),
                        }
                        for item in self._items
                    ]
                }
        return ret

    @staticmethod
    def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)
        assert uri.type == Playlist

        offset = 0
        limit = 100
        endpoint = connection.add_parameters_to_endpoint(
            "playlists/{playlist_id}".format(playlist_id=uri.id),
            fields="uri,description,name,images,owner(uri,display_name),snapshot_id,public,tracks(next,items(added_at,track(name,uri,is_local)))",
            offset=offset,
            limit=limit,
        )

        if (response := connection.make_request("GET", endpoint)) is not None:
            data = response
        else:
            raise SpotifyException("api request got no data")

        # check for long data that needs paging
        if data["tracks"]["next"] is not None:
            while True:
                offset += limit
                endpoint = connection.add_parameters_to_endpoint(
                    "playlists/{playlist_id}/tracks".format(playlist_id=uri.id),
                    fields="next,items(added_at,track(name,uri,is_local))",
                    offset=offset,
                    limit=limit,
                )
                if (response := connection.make_request("GET", endpoint)) is not None:
                    extra_data = response
                else:
                    raise SpotifyException("api request got no data")
                data["tracks"]["items"] += extra_data["items"]

                if extra_data["next"] is None:
                    break

        data["requested_time"] = time.time()

        return data

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._requested_time = data["requested_time"]
        if (not data["fetched"]) and (
            self._snapshot_id is not None
            and self._snapshot_id != data["snapshot_id"]
            or self.is_expired()
        ):
            raise ElementOutdated()

        self._name = data["name"]
        self._snapshot_id = data["snapshot_id"]
        self._description = data["description"]
        self._public = data["public"]
        self._owner = self._cache.get_user(
            uri=URI(data["owner"]["uri"]), display_name=data["owner"]["display_name"]
        )
        self._images = data["images"]
        self._items = []
        for track_to_add in data["tracks"]["items"]:
            if track_to_add["track"] is None or track_to_add["track"].get("is_local"):
                continue
            self._items.append(
                {
                    "track": self._cache.get_element(
                        uri=URI(track_to_add["track"]["uri"]),
                        name=track_to_add["track"]["name"],
                    ),
                    "added_at": track_to_add["added_at"],
                }
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
    def description(self) -> str:
        if self._description is None:
            self._cache.load(uri=self._uri)
        if self._description is not None:
            return self._description
        raise Exception("unreachable")

    @property
    def owner(self) -> User:
        if self._owner is None:
            self._cache.load(uri=self._uri)
        if self._owner is not None:
            return self._owner
        raise Exception("unreachable")

    @property
    def snapshot_id(self) -> str:
        if self._snapshot_id is None:
            self._cache.load(uri=self._uri)
        if self._snapshot_id is not None:
            return self._snapshot_id
        raise Exception("unreachable")

    @property
    def public(self) -> bool:
        if self._public is None:
            self._cache.load(uri=self._uri)
        if self._public is not None:
            return self._public
        raise Exception("unreachable")

    @property
    def items(self) -> list[Track | Episode]:
        if self._items is None:
            self._cache.load(uri=self._uri)
        if self._items is not None:
            return [item["track"] for item in self._items]
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

    def search(self, *strings: str) -> list[Playable]:
        """
        Search for the strings in the song titles. Only returns exact matches for all strings.

        :param strings: strings to search for
        :return: list of Tracks and Episodes
        """
        if self._items is None:
            self._cache.load(uri=self._uri)
        results = []
        strings = [string.lower() for string in strings]
        for item in self._items:
            song_title = item["track"].name.lower()

            do_append = True
            for string in strings:
                # on fail
                if song_title.find(string) == -1:
                    do_append = False
                    break

            if do_append:
                results.append(item["track"])

        return results


from .track import Track
from .episode import Episode
