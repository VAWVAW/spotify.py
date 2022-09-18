from __future__ import annotations
from abc import ABC, abstractmethod


class Cacheable(ABC):
    def __init__(self, uri: URI, cache: Cache, name: str = None, **kwargs):
        assert isinstance(uri, URI)
        assert isinstance(cache, Cache)
        assert isinstance(name, (str | None))
        self._uri = uri
        self._name = name
        self._cache = cache

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

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
    def to_dict(self, short: bool = False, minimal: bool = False) -> dict:
        pass

    @staticmethod
    @abstractmethod
    def make_request(uri: URI, connection: Connection) -> dict:
        pass

    @abstractmethod
    def is_expired(self) -> bool:
        pass


class Playable(Cacheable, ABC):
    @property
    @abstractmethod
    def images(self) -> list[dict[str, (int, str, None)]]:
        """
        get list of the image registered with spotify in different sizes

        :return: [{'height': (int | None), 'width': (int | None), 'url': str}]
        """
        pass


class PlayContext(Cacheable, ABC):
    @property
    @abstractmethod
    def images(self) -> list[dict[str, (int, str, None)]]:
        """
        get list of the image registered with spotify in different sizes

        :return: [{'height': (int | None), 'width': (int | None), 'url': str}]
        """
        pass

    @property
    @abstractmethod
    def items(self) -> list[(Playable | Track | Episode)]:
        pass


from .uri import URI
from .connection import Connection
from .cache import Cache
from .track import Track
from .episode import Episode
