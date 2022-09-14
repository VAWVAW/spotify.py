import json
from typing import Type

from .connection import Connection
from .cache import Cache
from .user import User
from .playlist import Playlist
from .track import Track
from .uri import URI
from .abc import Playable, PlayContext, Cacheable
from .errors import BadRequestException
from .episode import Episode
from .album import Album
from .artist import Artist
from .show import Show
from .authentication import Authentication
from .me import Me, SavedTracks


def _process_uri(uri: (str | URI)) -> URI:
    assert isinstance(uri, (str | URI))
    if isinstance(uri, URI):
        return uri
    return URI(uri_string=uri)


class Client:
    """
    standard interface to the api

    :param authentication: Authentication object for client authentication
    :param cache_dir: global path to the directory that this library should cache data in (note that sensitive data you request may be cached, set to None to disable caching)
    """
    def __init__(self, authentication: Authentication, cache_dir: str = None):
        assert isinstance(cache_dir, (str | None))
        assert isinstance(authentication, Authentication)

        self._connection = Connection(authentication=authentication)
        self._cache = Cache(connection=self._connection, cache_dir=cache_dir)

    def get_authentication_data(self) -> dict[str, (str | int | None)]:
        """
        Dump the authentication data for safe caching

        :return: { "client_id": client_id, "client_secret": client_secret, "scope": str(scope), "refresh_token": refresh_token, "show_dialog": show_dialog, "token": token, "expires": int(expires) }
        """
        return self._connection.dump_token_data()

    def play(self, elements: list[(URI | Playable | str)] = None, context: (URI | PlayContext | str) = None, offset: int = None, position_ms: int = None, device_id: str = None):
        """
        resume playback or play specified resource
        only one of albums and context may be specified

        :param elements: list of spotify uris or Playable types to play (None to resume playing)
        :param context: uri or PlayContext to use as context (e.g. playlist or album)
        :param offset: number of song in resource to start playing (only used if context_uri is set)
        :param position_ms: position in song to seek (only used if context_uri is set)
        :param device_id: device to target (None to use currently active device
        :raises SpotifyException: errors according to http response status
        """
        assert isinstance(elements, (list | None))
        assert isinstance(context, (URI | PlayContext | str | None))
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
            data["context_uri"] = str(context.uri if isinstance(context, PlayContext) else context)
            send_payload = True

        if elements is not None:
            if send_payload:
                raise BadRequestException("only one of albums and context may be specified")
            data["uris"] = []
            for element in elements:
                assert isinstance(element, (URI | Playable | str))
                data["uris"].append(str(element.uri if isinstance(element, Playable) else element))
            send_payload = True

        if send_payload:
            # play specified resource
            self._connection.make_request(method="PUT", endpoint=endpoint, data=json.dumps(data))
        else:
            # resume whatever was playing
            self._connection.make_request(method="PUT", endpoint=endpoint)

    def pause(self, device_id: str = None):
        """
        pause playback

        :param device_id: device to target (None to use currently active device
        :raises SpotifyException: errors according to http response status
        """
        assert isinstance(device_id, (str | None))

        endpoint = self._connection.add_parameters_to_endpoint("me/player/pause", device_id=device_id)

        self._connection.make_request(method="PUT", endpoint=endpoint)

    def next(self, device_id: str = None):
        """
        skip to next track in queue

        :param device_id:
        :raises SpotifyException: errors according to http response status
        """
        assert isinstance(device_id, (str | None))

        endpoint = self._connection.add_parameters_to_endpoint("me/player/next", device_id=device_id)

        self._connection.make_request(method="POST", endpoint=endpoint)

    def prev(self, device_id: str = None):
        """
        skip to previous track in queue

        :param device_id:
        :raises SpotifyException: errors according to http response status
        """
        assert isinstance(device_id, (str | None))

        endpoint = self._connection.add_parameters_to_endpoint("me/player/previous", device_id=device_id)

        self._connection.make_request(method="POST", endpoint=endpoint)

    def set_playback_shuffle(self, state: bool = True, device_id: str = None):
        """
        set shuffle mode on the specified device

        :param state: whether to activate shuffle
        :param device_id: device to target (None to use active device
        :raises SpotifyException: errors according to http response status
        """
        assert isinstance(state, bool)
        assert isinstance(device_id, (str | None))

        endpoint = self._connection.add_parameters_to_endpoint("me/player/shuffle", device_id=device_id, state=state)

        self._connection.make_request(method="PUT", endpoint=endpoint)

    def add_to_queue(self, element: (URI | Playable), device_id: str = None):
        """
        add uri to queue

        :param element: resource to add to queue
        :param device_id: device to target (None to use currently active device
        :raises SpotifyException: errors according to http response status
        """
        assert isinstance(element, (URI | Playable))
        assert isinstance(device_id, (str | None))

        endpoint = self._connection.add_parameters_to_endpoint("me/player/queue", device_id=device_id, uri=str(element if isinstance(element, URI) else element.uri))
        self._connection.make_request(method="POST", endpoint=endpoint)

    @property
    def devices(self) -> list[dict[str, (str | bool | int)]]:
        """
        return a list of all devices registered in spotify connect
        """
        endpoint = "me/player/devices"
        data = self._connection.make_request(method="GET", endpoint=endpoint)
        return data["devices"]

    def transfer_playback(self, device_id: str, play: bool = False):
        """
        transfer playback to new device

        :param device_id: id of targeted device
        :param play: whether to start playing on new device
        """
        assert isinstance(device_id, (str | None))
        assert isinstance(play, bool)

        endpoint = "me/player"
        self._connection.make_request(method="PUT", endpoint=endpoint, data=json.dumps({"device_ids": [device_id], "play": play}))

    def get_playing(self) -> (dict | None):
        """
        returns information to playback state

        :return: dict with is_playing, device, repeat_state, shuffle_state, context(playlist), item(track), actions
        """
        endpoint = "me/player"

        data = self._connection.make_request(method="GET", endpoint=endpoint)
        if data is None:
            return None

        data["item"] = self.get_element_from_data(data["item"])
        if data["context"] is not None:
            data["context"] = self.get_element_from_data(data["context"], check_outdated=False)
        return data

    @property
    def me(self) -> Me:
        """
        get the profile of the user who is authenticated

        :return: user profile
        """

        return self._cache.get_me()

    @property
    def user_playlists(self) -> list[Playlist]:
        """
        get playlists of current user

        :return: list of playlists saved in the user profile
        """

        return self._cache.get_me().playlists

    @property
    def saved_tracks(self) -> SavedTracks:
        """
        get tracks of current user

        :return: list of tracks saved in the user profile
        """

        return self._cache.get_saved_tracks()

    def get_element_from_data(self, data: dict = None, check_outdated: bool = False) -> Type[Playlist | User | Episode | Track | Album | Artist | Show]:
        """
        return the element with the matching uri
        :param data: dict with spotify data you got from caching something yourself
        :param check_outdated: whether to check if the element is outdated by refetching it
        """

        assert "uri" in data.keys()
        uri = URI(data["uri"])
        name = data["name"] if "name" in data.keys() else None
        display_name = data["display_name"] if "display_name" in data.keys() else None
        snapshot_id = data["snapshot_id"] if "snapshot_id" in data.keys() else None

        return self._cache.get_element(uri=uri, name=name, display_name=display_name, shapshot_id=snapshot_id, check_outdated=check_outdated)

    def get_element(self, uri: (URI | str), check_outdated: bool = True, **kwargs) -> Type[Playlist | User | Episode | Track | Album | Artist | Show]:
        """
        return the element with the matching uri
        :param uri: uri of the element
        :param check_outdated: see :py:meth:`~spotifython.Client.get_playlist`
        """

        uri = _process_uri(uri=uri)

        return self._cache.get_element(uri=uri, check_outdated=check_outdated,  **kwargs)

    def get_playlist(self, uri: (URI | str), check_outdated: bool = True, **kwargs) -> Playlist:
        """
        return Playlist object with the given uri

        :param uri: uri of the playlist
        :param check_outdated: whether to check if the playlist is outdated; True can lead to excessive api calls if the snapshot id is not found
        """
        uri = _process_uri(uri=uri)

        return self._cache.get_playlist(uri=uri, check_outdated=check_outdated, **kwargs)

    def get_album(self, uri: (URI | str), **kwargs) -> Album:
        """
        return Album object with the given uri

        :param uri: uri of the album
        """
        uri = _process_uri(uri=uri)

        return self._cache.get_album(uri=uri, **kwargs)

    def get_show(self, uri: (URI | str), **kwargs) -> Show:
        """
        return Show object with the given uri

        :param uri: uri of the Show
        """
        uri = _process_uri(uri=uri)

        return self._cache.get_show(uri=uri, **kwargs)

    def get_episode(self, uri: (URI | str), **kwargs) -> Episode:
        """
        return Episode object with the given uri

        :param uri: uri of the episode
        """
        uri = _process_uri(uri=uri)

        return self._cache.get_episode(uri=uri, **kwargs)

    def get_track(self, uri: (str | URI), **kwargs) -> Track:
        """
        return Track object with the given uri

        :param uri: uri of the track
        """
        uri = _process_uri(uri=uri)

        return self._cache.get_track(uri=uri, **kwargs)

    def get_artist(self, uri: (URI | str), **kwargs) -> Artist:
        """
        return Artist object with the given uri

        :param uri: uri of the artist
        """
        uri = _process_uri(uri=uri)

        return self._cache.get_artist(uri=uri, **kwargs)

    def get_user(self, uri: (str | URI), **kwargs) -> User:
        """
        return User object with the given uri

        :param uri: uri of the user
        """
        uri = _process_uri(uri=uri)

        return self._cache.get_user(uri=uri, **kwargs)

    def search(self, query: str, element_type: str, limit: int = 5, offset: int = 0) -> dict[str, list[Cacheable]]:
        """
        search for item

        :param query: string to search
        :param element_type: comma-separated list of return types; possible values: "album" "artist" "playlist" "track" "episode" "show"
        :param limit: number of results to return per type
        :param offset: offset of results per type
        :return: dict with types as keys and lists as albums
        """
        assert isinstance(query, str)
        assert isinstance(element_type, str)
        assert isinstance(limit, int)
        assert isinstance(offset, int)

        endpoint = self._connection.add_parameters_to_endpoint(
            "search",
            offset=offset,
            limit=limit,
            q=query,
            type=element_type
        )
        data = self._connection.make_request(method="GET", endpoint=endpoint)
        types = element_type.split(",")
        ret = {}
        for element_type in types:
            element_type += "s"
            ret[element_type] = []
            for element in data[element_type]["items"]:
                ret[element_type].append(self._cache.get_element(uri=URI(element["uri"])))
                ret[element_type][-1].load_dict(data=element)
        return ret

    def search_track(self, query: str, limit: int = 5, offset: int = 0) -> list[Track]:
        """
        search for track

        :param query: string to search
        :param limit: number of results to return
        :param offset: offset of results
        :return: list of the found tracks
        """
        elements = (self.search(query=query, element_type="track", offset=offset, limit=limit))["tracks"]
        for element in elements:
            assert isinstance(element, Track), "got invalid search result"
        # noinspection PyTypeChecker
        return elements

    def search_episode(self, query: str, limit: int = 5, offset: int = 0) -> list[Episode]:
        """
        search for episode

        :param query: string to search
        :param limit: number of results to return
        :param offset: offset of results
        :return: list of the found albums
        """
        elements = (self.search(query=query, element_type="episode", offset=offset, limit=limit))["albums"]
        for element in elements:
            assert isinstance(element, Episode), "got invalid search result"
        # noinspection PyTypeChecker
        return elements

    def search_playlist(self, query: str, limit: int = 5, offset: int = 0) -> list[Playlist]:
        """
        search for playlist

        :param query: string to search
        :param limit: number of results to return
        :param offset: offset of results
        :return: list of the found playlists
        """
        elements = (self.search(query=query, element_type="playlist", offset=offset, limit=limit))["playlists"]
        for element in elements:
            assert isinstance(element, Playlist), "got invalid search result"
        # noinspection PyTypeChecker
        return elements

    def search_album(self, query: str, limit: int = 5, offset: int = 0) -> list[Album]:
        """
        search for album

        :param query: string to search
        :param limit: number of results to return
        :param offset: offset of results
        :return: list of the found albums
        """
        elements = (self.search(query=query, element_type="album", offset=offset, limit=limit))["albums"]
        for element in elements:
            assert isinstance(element, Album), "got invalid search result"
        # noinspection PyTypeChecker
        return elements

    def search_artist(self, query: str, limit: int = 5, offset: int = 0) -> list[Artist]:
        """
        search for artist

        :param query: string to search
        :param limit: number of results to return
        :param offset: offset of results
        :return: list of the found artists
        """
        elements = (self.search(query=query, element_type="artist", offset=offset, limit=limit))["artists"]
        for element in elements:
            assert isinstance(element, Artist), "got invalid search result"
        # noinspection PyTypeChecker
        return elements

    def search_user(self, query: str, limit: int = 5, offset: int = 0) -> list[User]:
        """
        search for user

        :param query: string to search
        :param limit: number of results to return
        :param offset: offset of results
        :return: list of the found users
        """
        elements = (self.search(query=query, element_type="user", offset=offset, limit=limit))["users"]
        for element in elements:
            assert isinstance(element, User), "got invalid search result"
        # noinspection PyTypeChecker
        return elements

    def search_show(self, query: str, limit: int = 5, offset: int = 0) -> list[Show]:
        """
        search for show

        :param query: string to search
        :param limit: number of results to return
        :param offset: offset of results
        :return: list of the found users
        """
        elements = (self.search(query=query, element_type="show", offset=offset, limit=limit))["albums"]
        for element in elements:
            assert isinstance(element, User), "got invalid search result"
        # noinspection PyTypeChecker
        return elements

    def search_playable(self, query: str, limit: int = 5, offset: int = 0) -> list[Playable]:
        """
        search for playable

        :param query: string to search
        :param limit: number of results to return
        :param offset: offset of results
        :return: list of the found playables
        """
        data = self.search(query=query, element_type="track,episode", offset=offset, limit=limit)
        elements = data["tracks"] + data["albums"]
        for element in elements:
            assert isinstance(element, Playable), "got invalid search result"
        # noinspection PyTypeChecker
        return elements
