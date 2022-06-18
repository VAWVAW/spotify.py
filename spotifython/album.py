from .abc import PlayContext
from .uri import URI
from .cache import Cache
from .connection import Connection
from .track import Track
from .artist import Artist


class Album(PlayContext):
    """
    Do not create an object of this class yourself. Use :meth:`spotifython.Client.get_album` instead.
    """
    def __init__(self, uri: URI, cache: Cache, name: str = None, **kwargs):
        super().__init__(uri=uri, cache=cache, name=name, **kwargs)

        self._artists = None
        self._items = None
        self._images = None

    def to_dict(self, short: bool = False, minimal: bool = False) -> dict:
        ret = {"uri": str(self._uri)}
        if self._name is not None: ret["name"] = self._name

        if not minimal:
            if self._items is None:
                self._cache.load(self.uri)

            ret["images"] = self._images
            ret["name"] = self._name
            ret["artists"] = [
                {
                    "uri": str(artist.uri),
                    "name": artist.name
                }
                for artist in self._artists
            ]

            if not short:
                ret["tracks"] = {
                    "items": [
                        {
                            "uri": str(item.uri),
                            "name": item.name
                        }
                        for item in self._items
                    ]
                }
        return ret

    @staticmethod
    def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)
        assert uri.type == Album

        offset = 0
        limit = 50
        endpoint = connection.add_parameters_to_endpoint(
            "albums/{id}".format(id=uri.id),
            offset=offset,
            limit=limit
        )

        data = connection.make_request("GET", endpoint)

        # check for long data that needs paging
        if data["tracks"]["next"] is not None:
            while True:
                offset += limit
                endpoint = connection.add_parameters_to_endpoint(
                    "albums/{id}/tracks".format(id=uri.id),
                    offset=offset,
                    limit=limit
                )
                extra_data = connection.make_request("GET", endpoint)
                data["tracks"]["items"] += extra_data["items"]

                if extra_data["next"] is None:
                    break
        return data

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        self._name = data["name"]
        self._images = data["images"]
        self._items = []
        self._artists = []

        for track in data["tracks"]["items"]:
            if track is None:
                continue
            self._items.append(self._cache.get_track(uri=URI(track["uri"]), name=track["name"]))

        for artist in data["artists"]:
            if artist is None:
                continue
            self._artists.append(self._cache.get_artist(uri=URI(artist["uri"]), name=artist["name"]))

    @property
    def items(self) -> list[Track]:
        if self._items is None:
            self._cache.load(uri=self._uri)
        return self._items.copy()

    @property
    def tracks(self) -> list[Track]:
        if self._items is None:
            self._cache.load(uri=self._uri)
        return self._items.copy()

    @property
    def artists(self) -> list[Artist]:
        if self._artists is None:
            self._cache.load(uri=self._uri)
        return self._artists.copy()

    @property
    def images(self) -> list[dict[str, (str, int, None)]]:
        """
        get list of the image registered with spotify in different sizes

        :return: [{'height': (int | None), 'width': (int | None), 'url': str}]
        """
        if self._images is None:
            self._cache.load(uri=self._uri)
        return self._images.copy()

    # TODO add search
