# resolve circular dependencies
from __future__ import annotations

from typing import Type


class URI:
    """
    A simple wrapper for the uri sting.
    """
    def __init__(self, uri_string: str):
        assert isinstance(uri_string, str)
        uri_elements = uri_string.split(":")
        assert len(uri_elements) >= 3 and uri_elements[0] == "spotify", 'invalid uri string (not in format "spotify:<element_type>:<id>")'

        self._uri_string = uri_string

        self._id = uri_elements[2]
        if len(uri_elements) == 3:
            self._type = datatypes[uri_elements[1]]
        if len(uri_elements) == 4:
            if uri_elements[1] == "user" and uri_elements[3] == "collection":
                self._type = SavedTracks

    def __str__(self):
        """
        :return: uri as string
        """
        return self._uri_string

    @property
    def id(self) -> str:
        """
        :return: id of the element
        """
        return self._id

    @property
    def type(self) -> Type[Playlist | User | Episode | Track | Album | Artist | Show | SavedTracks | PlayContext]:
        """
        :return: type of the element
        """
        return self._type


from .user import User
from .playlist import Playlist
from .episode import Episode
from .track import Track
from .artist import Artist
from .album import Album
from .show import Show
from .datatypes import datatypes
from .me import SavedTracks
from .abc import PlayContext
