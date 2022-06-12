from __future__ import annotations
from abc import ABC, abstractmethod


class Cacheable(ABC):
    def __init__(self, uri: URI, cache: Cache, name: str = None):
        assert isinstance(uri, URI)
        assert isinstance(cache, Cache)
        assert isinstance(name, (str | None))
        self._uri = uri
        self._name = name
        self._cache = cache

    @property
    def uri(self) -> URI:
        return self._uri

    @property
    def name(self) -> str:
        if self._name is None:
            self._cache.load(self._uri)
        return self._name

    @abstractmethod
    def load_dict(self, data: dict):
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @staticmethod
    @abstractmethod
    def make_request(uri: URI, connection: Connection) -> dict:
        pass


class Playable(Cacheable, ABC):
    @property
    @abstractmethod
    def images(self) -> list[dict[str, (int, str, None)]]:
        pass


class PlayContext(Cacheable, ABC):
    pass


from .uri import URI
from .connection import Connection
from .cache import Cache
