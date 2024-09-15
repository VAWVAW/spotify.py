# resolve circular dependencies
from __future__ import annotations
from abc import ABCMeta


class URI:
    """
    A simple wrapper for the uri sting.
    """

    def __init__(self, uri_string: str):
        assert isinstance(uri_string, str)
        uri_elements = uri_string.split(":")
        assert (
            len(uri_elements) >= 3 and uri_elements[0] == "spotify"
        ), 'invalid uri string (not in format "spotify:<element_type>:<id>")'

        self._uri_string: str = uri_string

        self._id: str = uri_elements[2]
        if len(uri_elements) == 3:
            self._type: ABCMeta = datatypes[uri_elements[1]]
        if len(uri_elements) == 4:
            if uri_elements[1] == "user" and uri_elements[3] == "collection":
                self._type = SavedTracks

    def __str__(self) -> str:
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
    def type(
        self,
    ) -> ABCMeta:
        """
        :return: type of the element
        """
        return self._type


from .datatypes import datatypes
from .me import SavedTracks
