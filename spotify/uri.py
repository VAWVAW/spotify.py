# resolve circular dependencies
from __future__ import annotations


class URI:
    def __init__(self, uri: str):
        sts = uri.split(":")
        assert len(sts) == 3

        self._type = sts[1]
        self._id = sts[2]

    @classmethod
    def from_values(cls, type: str, id: str) -> URI:
        new_uri = cls.__new__(cls)
        new_uri._type = type
        new_uri._id = id
        return new_uri

    def __str__(self):
        return "spotify:" + self._type + ":" + self._id

    @property
    def id(self) -> str:
        return self._id

    @property
    def type(self) -> str:
        return self._type
