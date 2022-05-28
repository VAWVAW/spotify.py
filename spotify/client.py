import json
import os

from typing import List

from .connection import Connection
from .cache import Cache
from .playlist import Playlist
from .track import Track
from .user import User
from .uri import URI
from .abc import Playable, PlayContext
from .errors import BadRequestException


class SpotifyClient:
    def __init__(self, cache_dir: str = None):
        self._connection = Connection()
        self._cache = Cache(connection=self._connection, cache_dir=cache_dir)
        self._playlists = None

    async def play(self, elements: List[(URI | Playable)] = None, context: (URI | PlayContext) = None, offset: int = None, position_ms: int = None, device_id: str = None) -> None:
        """
        resume playback or play specified resource\n
        only one of elements and context may be specified\n\n
        examples:\n
        await SpotifyClient.play()\n
        await SpotifyClient.play(context="spotify:album:5ht7ItJgpBH7W6vJ5BqpPr", offset=5, position_ms=1000)

        :param elements: list of spotify uris or Playable types to play (leave at None to resume playing)
        :param context: uri or PlayContext to use as context (e.g. playlist or album)
        :param offset: number of song in resource to start playing (only used if context_uri is set)
        :param position_ms: position in song to seek (only used if context_uri is set)
        :param device_id: device to target (leave at None to use currently active device
        :raises SpotifyException: errors according to http response status
        """
        assert isinstance(elements, (list | None))
        assert isinstance(context, (URI | PlayContext))
        assert isinstance(offset, (int | None))
        assert isinstance(position_ms, (int | None))
        assert isinstance(device_id, (str | None))

        data = {}
        send_payload = False

        endpoint = self._connection.add_parameters_to_endpoint("me/player/play", device_id=device_id)

        if offset is not None:
            data["offset"] = {"position": offset}
        if position_ms is not None:
            data["position_ms"] = position_ms

        if context is not None:
            data["context_uri"] = str(context if isinstance(context, URI) else await context.uri)
            send_payload = True

        if elements is not None:
            if send_payload:
                raise BadRequestException("only one of elements and context may be specified")
            data["uris"] = []
            for element in elements:
                assert isinstance(element, (URI | Playable))
                data["uris"].append(str(element if isinstance(element, URI) else await element.uri))
            send_payload = True

        if send_payload:
            # play specified resource
            await self._connection.make_put_request(endpoint=endpoint, data=json.dumps(data))
        else:
            # resume whatever was playing
            await self._connection.make_put_request(endpoint=endpoint)

    async def pause(self, device_id: str = None) -> None:
        """
        pause playback

        :param device_id: device to target (leave at None to use currently active device
        :raises SpotifyException: errors according to http response status
        """
        assert isinstance(device_id, (str | None))

        endpoint = self._connection.add_parameters_to_endpoint("me/player/pause", device_id=device_id)

        await self._connection.make_put_request(endpoint=endpoint)

    async def set_playback_shuffle(self, state: bool = True, device_id: str = None) -> None:
        """
        set shuffle mode on the specified device

        :param state: whether to activate shuffle
        :param device_id: device to target (leave at None to use currently active device
        :raises SpotifyException: errors according to http response status
        """
        assert isinstance(state, bool)
        assert isinstance(device_id, (str | None))

        endpoint = self._connection.add_parameters_to_endpoint("me/player/shuffle", device_id=device_id, state=state)

        await self._connection.make_put_request(endpoint=endpoint)

    async def add_to_queue(self, element: (URI | Playable), device_id: str = None) -> None:
        """
        add uri to queue \n\n
        example: \n
        await SpotifyClient.add_to_queue("spotify:track:4iV5W9uYEdYUVa79Axb7Rh")

        :param element: resource to add to queue
        :param device_id: device to target (leave at None to use currently active device
        :raises SpotifyException: errors according to http response status
        """
        assert isinstance(element, (URI | Playable))
        assert isinstance(device_id, (str | None))

        endpoint = self._connection.add_parameters_to_endpoint("me/player/queue", device_id=device_id, uri=str(element if isinstance(element, URI) else await element.uri))
        await self._connection.make_post_request(endpoint=endpoint)

    async def close(self) -> None:
        """
        clean session and exit
        """
        await self._connection.close()

    async def get_devices(self) -> List[dict]:
        """
        return a list of all devices registered in spotify connect
        """
        endpoint = "me/player/devices"
        data = await self._connection.make_get_request(endpoint=endpoint)
        return data["devices"]

    async def transfer_playback(self, device_id: str, play: bool = False) -> None:
        """
        transfer playback to new device
        :param device_id: id of targeted device
        :param play: whether to start playing on new device
        """
        assert isinstance(device_id, (str | None))
        assert isinstance(play, bool)

        endpoint = "me/player"
        await self._connection.make_put_request(endpoint=endpoint, data=json.dumps({"device_ids": [device_id], "play": play}))

    async def _fetch_playlists(self) -> dict:
        # TODO add album fetch
        offset = 0
        limit = 50
        endpoint = self._connection.add_parameters_to_endpoint("me/playlists", offset=offset, limit=limit, fields="items(uri,name,snapshot_id)")

        data = await self._connection.make_get_request(endpoint=endpoint)

        # check for long data that needs paging
        if data["next"] is not None:
            while True:
                offset += limit
                endpoint = self._connection.add_parameters_to_endpoint(
                    "me/playlists",
                    fields="items(uri,name,snapshot_id)",
                    offset=offset,
                    limit=limit
                )
                extra_data = await self._connection.make_get_request(endpoint)
                data["items"] += extra_data["items"]

                if extra_data["next"] is None:
                    break
        return data

    async def load_user(self) -> None:
        """
        load user data from cache if possible
        """
        cache_after = False
        # try to load from cache
        if self._cache.cache_dir is not None:
            path = os.path.join(self._cache.cache_dir, "user")
            try:
                # load from cache
                with open(path, "r") as in_file:
                    data = json.load(in_file)
            except (FileNotFoundError, json.JSONDecodeError):
                # request new data
                data = {"playlists": await self._fetch_playlists()}
                cache_after = True
        else:
            data = {"playlists": await self._fetch_playlists()}

        self._playlists = []
        for playlist in data["playlists"]["items"]:
            self._playlists.append(self._cache.get_playlist(uri=URI(playlist["uri"]), name=playlist["name"], snapshot_id=playlist["snapshot_id"]))

        if cache_after:
            pass
            # TODO cache user playlists
            # await self._cache_self()

    async def user_playlists(self) -> List[Playlist]:
        """
        get playlists of current user
        :return: list of playlists saved in the user profile
        """
        if self._playlists is None:
            await self.load_user()

        return self._playlists.copy()

    async def get_playlist(self, uri: URI) -> Playlist:
        """
        return Playlist object for the given id
        :param uri: uri of the playlist
        """
        assert isinstance(uri, URI)

        return self._cache.get_playlist(uri=uri)

    async def get_track(self, uri: URI) -> Track:
        """
        return Track object for the given id
        :param uri: uri of the track
        """
        assert isinstance(uri, URI)

        return self._cache.get_track(uri=uri)

    async def get_user(self, uri: URI) -> User:
        """
        return User object for the given id
        :param uri: uri of the user
        """
        assert isinstance(uri, URI)

        return self._cache.get_user(uri=uri)

    async def get_playing(self) -> dict:
        """
        returns information to playback state
        :return: dict with is_playing, device, repeat_state, shuffle_state, context(playlist), item(track), actions
        """
        endpoint = "me/player"

        return await self._connection.make_get_request(endpoint=endpoint)

# TODO add album support
