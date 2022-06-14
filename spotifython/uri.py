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
        assert len(uri_elements) == 3 and uri_elements[0] == "spotify", 'invalid uri string (not in format "spotify:<element_type>:<id>")'

        self._type = datatypes[uri_elements[1]]
        self._type_str = uri_elements[1]
        self._id = uri_elements[2]

    def __str__(self):
        """
        :return: uri as string
        """
        return "spotify:" + self._type_str + ":" + self._id

    @property
    def id(self) -> str:
        """
        :return: id of the element
        """
        return self._id

    @property
    def type(self) -> Type[Playlist | User | Episode | Track | Album | Artist | Show]:
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
