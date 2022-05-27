import json

from typing import List

from .connection import Connection
from .cache import Cache
from .playlist import Playlist


class SpotifyClient:
    def __init__(self, cache_dir: str = None):
        self._connection = Connection()
        self._cache = Cache(connection=self._connection, cache_dir=cache_dir)
        self._playlists = None

    async def play(self, context_uri: str = None, offset: int = None, position_ms: int = None, device_id: str = None) -> None:
        """
        resume playback or play specified resource\n\n
        examples:\n
        await SpotifyClient.play()\n
        await SpotifyClient.play(context_uri="spotify:album:5ht7ItJgpBH7W6vJ5BqpPr", offset=5, position_ms=1000)

        :param context_uri: spotify uri to resource to play (leave at None to resume playing)
        :param offset: number of song in resource to start playing (only used if context_uri is set)
        :param position_ms: position in song to seek (only used if context_uri is set)
        :param device_id: device to target (leave at None to use currently active device
        :raises SpotifyException: errors according to http response status
        """
        data = {}
        endpoint = self._connection.add_parameters_to_endpoint("me/player/play", device_id=device_id)

        if offset is not None:
            data["offset"] = {"position": offset}
        if position_ms is not None:
            data["position_ms"] = position_ms

        if context_uri is None:
            # resume whatever was playing
            await self._connection.make_put_request(endpoint=endpoint)
        else:
            # play specified resource
            await self._connection.make_put_request(endpoint=endpoint, data=json.dumps(data))

    async def pause(self, device_id: str = None) -> None:
        """
        pause playback

        :param device_id: device to target (leave at None to use currently active device
        :raises SpotifyException: errors according to http response status
        """

        endpoint = self._connection.add_parameters_to_endpoint("me/player/pause", device_id=device_id)

        await self._connection.make_put_request(endpoint=endpoint)

    async def set_playback_shuffle(self, state: bool = True, device_id: str = None) -> None:
        """
        set shuffle mode on the specified device

        :param state: whether to activate shuffle
        :param device_id: device to target (leave at None to use currently active device
        :raises SpotifyException: errors according to http response status
        """

        endpoint = self._connection.add_parameters_to_endpoint("me/player/shuffle", device_id=device_id, state=state)

        await self._connection.make_put_request(endpoint=endpoint)

    async def add_to_queue(self, uri: str, device_id: str = None) -> None:
        """
        add uri to queue \n\n
        example: \n
        await SpotifyClient.add_to_queue("spotify:track:4iV5W9uYEdYUVa79Axb7Rh")

        :param uri: resource to add to queue
        :param device_id: device to target (leave at None to use currently active device
        :raises SpotifyException: errors according to http response status
        """

        endpoint = self._connection.add_parameters_to_endpoint("me/player/queue", device_id=device_id, uri=uri)

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
        endpoint = "me/player"
        await self._connection.make_put_request(endpoint=endpoint, data=json.dumps({"device_ids": [device_id], "play": play}))

    async def fetch_user(self) -> None:
        """
        fetch playlists and albums of current user
        """
        offset = 0
        limit = 50
        endpoint = self._connection.add_parameters_to_endpoint("me/playlists", offset=offset, limit=limit, fields="items(id,name)")

        data = await self._connection.make_get_request(endpoint=endpoint)

        # check for long data that needs paging
        if data["next"] is not None:
            while True:
                offset += limit
                endpoint = self._connection.add_parameters_to_endpoint(
                    "me/playlists",
                    fields="items(id,name)",
                    offset=offset,
                    limit=limit
                )
                extra_data = await self._connection.make_get_request(endpoint)
                data["items"] += extra_data["items"]

                if extra_data["next"] is None:
                    break

        self._playlists = []
        for playlist in data["items"]:
            self._playlists.append(self._cache.get_playlist(p_id=playlist["id"], name=playlist["name"]))

        # TODO add album fetch

    async def user_playlists(self) -> List[Playlist]:
        """
        get playlists of current user
        :return: list of playlists saved in the user profile
        """
        if self._playlists is None:
            await self.fetch_user()

        return self._playlists.copy()

# TODO add album and episode support
