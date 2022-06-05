import json

from .connection import Connection
from .cache import Cache
from .user import User
from .playlist import Playlist
from .track import Track
from .uri import URI
from .abc import Playable, PlayContext
from .errors import BadRequestException
from .scope import Scope


class SpotifyClient:
    def __init__(self, cache_dir: str = None, client_id: str = None, client_secret: str = None, scope: Scope = None, show_dialog: bool = False):
        """
        You need to request a token using SpotifyClient.request_token() to interact with the api.

        You need to register an application at https://developer.spotify.com/dashboard/applications and edit the settings to add "http://localhost:2342/" to the redirect uris to allow this library to request a token.
        If you want to use a token you generated yourself refer to SpotifyClient.set_token().
        :param client_id: the Client ID of the application
        :param client_secret: the Client Secret of the application (click on "SHOW CLIENT SECRET")
        :param scope: the Scope object reflecting the permissions you need
        :param show_dialog: whether to query the user every time a new refresh token is requested
        :param cache_dir: global path to the directory that this library should cache data in (note that sensitive data you request may be cached, set to None to disable caching)
        """
        assert isinstance(cache_dir, (str | None))
        assert isinstance(client_id, str)
        assert isinstance(client_secret, str)
        assert isinstance(scope, (Scope | None))

        self._connection = Connection()
        self._cache = Cache(connection=self._connection, cache_dir=cache_dir)
        self._cache.load_token(client_id=client_id, client_secret=client_secret, scope=scope, show_dialog=show_dialog)

    async def set_token(self, token: str):
        """
        use this method to use a token you generated elsewhere
        :param token: the Bearer token to use
        """
        assert isinstance(token, str)

        self._connection._token = token

    async def play(self, elements: list[(URI | Playable)] = None, context: (URI | PlayContext) = None, offset: int = None, position_ms: int = None, device_id: str = None):
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
        assert isinstance(context, (URI | PlayContext | None))
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
            await self._connection.make_request(method="PUT", endpoint=endpoint, data=json.dumps(data))
        else:
            # resume whatever was playing
            await self._connection.make_request(method="PUT", endpoint=endpoint)

    async def pause(self, device_id: str = None):
        """
        pause playback

        :param device_id: device to target (leave at None to use currently active device
        :raises SpotifyException: errors according to http response status
        """
        assert isinstance(device_id, (str | None))

        endpoint = self._connection.add_parameters_to_endpoint("me/player/pause", device_id=device_id)

        await self._connection.make_request(method="PUT", endpoint=endpoint)

    async def next(self, device_id: str = None):
        """
        skip to next track in queue

        :param device_id:
        :raises SpotifyException: errors according to http response status
        """
        assert isinstance(device_id, (str | None))

        endpoint = self._connection.add_parameters_to_endpoint("me/player/next", device_id=device_id)

        await self._connection.make_request(method="POST", endpoint=endpoint)

    async def prev(self, device_id: str = None):
        """
        skip to previous track in queue

        :param device_id:
        :raises SpotifyException: errors according to http response status
        """
        assert isinstance(device_id, (str | None))

        endpoint = self._connection.add_parameters_to_endpoint("me/player/previous", device_id=device_id)

        await self._connection.make_request(method="POST", endpoint=endpoint)

    async def set_playback_shuffle(self, state: bool = True, device_id: str = None):
        """
        set shuffle mode on the specified device

        :param state: whether to activate shuffle
        :param device_id: device to target (leave at None to use currently active device
        :raises SpotifyException: errors according to http response status
        """
        assert isinstance(state, bool)
        assert isinstance(device_id, (str | None))

        endpoint = self._connection.add_parameters_to_endpoint("me/player/shuffle", device_id=device_id, state=state)

        await self._connection.make_request(method="PUT", endpoint=endpoint)

    async def add_to_queue(self, element: (URI | Playable), device_id: str = None):
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
        await self._connection.make_request(method="POST", endpoint=endpoint)

    async def close(self):
        """
        clean session and exit
        """
        await self._connection.close()
        self._cache.close()

    async def get_devices(self) -> list[dict[str, (str | bool | int)]]:
        """
        return a list of all devices registered in spotify connect
        """
        endpoint = "me/player/devices"
        data = await self._connection.make_request(method="GET", endpoint=endpoint)
        return data["devices"]

    async def transfer_playback(self, device_id: str, play: bool = False):
        """
        transfer playback to new device
        :param device_id: id of targeted device
        :param play: whether to start playing on new device
        """
        assert isinstance(device_id, (str | None))
        assert isinstance(play, bool)

        endpoint = "me/player"
        await self._connection.make_request(method="PUT", endpoint=endpoint, data=json.dumps({"device_ids": [device_id], "play": play}))

    async def user_playlists(self) -> list[Playlist]:
        """
        get playlists of current user
        :return: list of playlists saved in the user profile
        """
        return await (await self._cache.get_me()).playlists

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

        return await self._connection.make_request(method="GET", endpoint=endpoint)
