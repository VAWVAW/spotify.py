from .connection import Connection
from .user import User
from .cache import Cache
from .uri import URI
from .abc import PlayContext, Playable
from .errors import ElementOutdated


class Playlist(PlayContext):
    def __init__(self, uri: URI, cache: Cache, name: str = None, snapshot_id: str = None):
        super().__init__(uri=uri, cache=cache, name=name)

        self._snapshot_id = snapshot_id

        self._description = None
        self._owner = None
        self._public = None
        self._items = None
        self._images = None

    async def to_dict(self) -> dict:
        return {
            "uri": str(self._uri),
            "description": self._description,
            "owner":
                {
                    "uri": str(await self._owner.uri),
                    "display_name": await self._owner.name
                },
            "images": self._images,
            "snapshot_id": self._snapshot_id,
            "name": self._name,
            "public": self._public,
            "tracks": {
                "items": [
                    {
                        "added_at": item["added_at"],
                        "track":{
                            "uri": str(await item["track"].uri),
                            "name": await item["track"].name
                        }
                    }
                    for item in self._items
                ]
            }
        }

    @staticmethod
    async def make_request(uri: URI, connection: Connection) -> dict:
        assert isinstance(uri, URI)
        assert isinstance(connection, Connection)
        assert uri.type == "playlist"

        offset = 0
        limit = 100
        endpoint = connection.add_parameters_to_endpoint(
            "playlists/{playlist_id}".format(playlist_id=uri.id),
            fields="uri,description,name,images,owner(uri,display_name),snapshot_id,public,tracks(next,items(added_at,track(name,uri)))",
            offset=offset,
            limit=limit
        )

        data = await connection.make_request("GET", endpoint)

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
                extra_data = await connection.make_request("GET", endpoint)
                data["tracks"]["items"] += extra_data["items"]

                if extra_data["next"] is None:
                    break

        return data

    def load_dict(self, data: dict):
        assert isinstance(data, dict)
        assert str(self._uri) == data["uri"]

        if self._snapshot_id != data["snapshot_id"] and not data["fetched"]:
            raise ElementOutdated()

        self._name = data["name"]
        self._snapshot_id = data["snapshot_id"]
        self._description = data["description"]
        self._public = data["public"]
        self._owner = self._cache.get_user(uri=URI(data["owner"]["uri"]), display_name=data["owner"]["display_name"])
        self._images = data["images"]
        self._items = []
        for track_to_add in data["tracks"]["items"]:
            if track_to_add["track"] is None:
                continue
            self._items.append({
                "track": self._cache.get_element(uri=URI(track_to_add["track"]["uri"]), name=track_to_add["track"]["name"]),
                "added_at": track_to_add["added_at"]
            })

    @property
    async def description(self) -> str:
        if self._description is None:
            await self._cache.load(uri=self._uri)
        return self._description

    @property
    async def owner(self) -> User:
        if self._owner is None:
            await self._cache.load(uri=self._uri)
        return self._owner

    @property
    async def snapshot_id(self) -> str:
        if self._snapshot_id is None:
            await self._cache.load(uri=self._uri)
        return self._snapshot_id

    @property
    async def public(self) -> bool:
        if self._public is None:
            await self._cache.load(uri=self._uri)
        return self._public

    @property
    async def items(self) -> list[dict[str, (Playable | str)]]:
        if self._items is None:
            await self._cache.load(uri=self._uri)
        return self._items.copy()

    @property
    async def images(self) -> list[dict[str, (str, int, None)]]:
        if self._images is None:
            await self._cache.load(uri=self._uri)
        return self._images.copy()

    async def search(self, *strings: str) -> list[Playable]:
        if self._items is None:
            await self._cache.load(uri=self._uri)
        results = []
        strings = [string.lower() for string in strings]
        for item in self._items:
            song_title = (await item["track"].name).lower()

            do_append = True
            for string in strings:
                # on fail
                if song_title.find(string) == -1:
                    do_append = False
                    break

            if do_append:
                results.append(item["track"])

        return results
