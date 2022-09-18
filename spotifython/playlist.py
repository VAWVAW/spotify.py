from __future__ import annotations

import time

from .connection import Connection
from .user import User
from .cache import Cache
from .uri import URI
from .abc import PlayContext, Playable
from .errors import ElementOutdated


class Playlist(PlayContext):
    """
    Do not create an object of this class yourself. Use :meth:`spotifython.Client.get_playlist` instead.
    """

    def __init__(self, uri: URI, cache: Cache, name: str = None, snapshot_id: str = None, check_outdated: bool = True, **kwargs):
        super().__init__(uri=uri, cache=cache, name=name, **kwargs)

        self._check_outdated = check_outdated
        self._snapshot_id = snapshot_id

        self._description = None
        self._owner = None
        self._public = None
        self._items = None
        self._images = None
        self._requested_time = None

    def to_dict(self, short: bool = False, minimal: bool = False) -> dict:
        ret = {"uri": str(self._uri)}
        if self._name is not None: ret["name"] = self._name
        if self._snapshot_id is not None: ret["snapshot_id"] = self._snapshot_id

        if not minimal:
            if self._items is None:
                self._cache.load(self.uri)

            ret["images"] = self._images
            ret["public"] = self._public
            ret["description"] = self._description
            ret["snapshot_id"] = self._snapshot_id
            ret["name"] = self._name
            ret["owner"] = self._owner.to_dict(minimal=True)
            ret["requested_time"] = self._requested_time

            if not short:
                ret["tracks"] = {
                    "items": [
                        {
                            "added_at": item["added_at"],
                            "track": item["track"].to_dict(minimal=True)
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
            fields="uri,description,name,images,owner(uri,display_name),snapshot_id,public,tracks(next,items(added_at,track(name,uri)))",
            offset=offset,
            limit=limit
        )

        data = connection.make_request("GET", endpoint)

        # check for long data that needs paging
        if data["tracks"]["next"] is not None:
            while True:
                offset += limit
                endpoint = connection.add_parameters_to_endpoint(
                    "playlists/{playlist_id}/tracks".format(playlist_id=uri.id),
                    fields="next,items(added_at,track(name,uri))",
                    offset=offset,
                    limit=limit
                )
                extra_data = connection.make_request("GET", endpoint)
                data["tracks"]["items"] += extra_data["items"]

                if extra_data["next"] is None:
                    break

        data["requested_time"] = time.time()

        return data

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        if self._check_outdated and self._snapshot_id != data["snapshot_id"] and not data["fetched"]:
            raise ElementOutdated()

        self._name = data["name"]
        self._snapshot_id = data["snapshot_id"]
        self._description = data["description"]
        self._public = data["public"]
        self._owner = self._cache.get_user(uri=URI(data["owner"]["uri"]), display_name=data["owner"]["display_name"])
        self._images = data["images"]
        self._items = []
        self._requested_time = data["requested_time"]
        for track_to_add in data["tracks"]["items"]:
            if track_to_add["track"] is None:
                continue
            self._items.append({
                "track": self._cache.get_element(uri=URI(track_to_add["track"]["uri"]), name=track_to_add["track"]["name"]),
                "added_at": track_to_add["added_at"]
            })

    def is_expired(self) -> bool:
        if self._requested_time is None:
            self._cache.load(uri=self._uri)
        return time.time() > self._requested_time + 514800  # one week in unix time

    @property
    def description(self) -> str:
        if self._description is None:
            self._cache.load(uri=self._uri)
        return self._description

    @property
    def owner(self) -> User:
        if self._owner is None:
            self._cache.load(uri=self._uri)
        return self._owner

    @property
    def snapshot_id(self) -> str:
        if self._snapshot_id is None:
            self._cache.load(uri=self._uri)
        return self._snapshot_id

    @property
    def public(self) -> bool:
        if self._public is None:
            self._cache.load(uri=self._uri)
        return self._public

    @property
    def items(self) -> list[(Track | Episode | Playable)]:
        if self._items is None:
            self._cache.load(uri=self._uri)
        return [item["track"] for item in self._items]

    @property
    def images(self) -> list[dict[str, (str, int, None)]]:
        """
        get list of the image registered with spotify in different sizes

        :return: [{'height': (int | None), 'width': (int | None), 'url': str}]
        """
        if self._images is None:
            self._cache.load(uri=self._uri)
        return self._images.copy()

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
