# -*- coding: utf-8 -*-

"""
Spotify API Wrapper
~~~~~~~~~~~~~~~~~~~

A basic wrapper for the Spotify API.

:copyright: (c) 2022-present VAWVAW
:license: GPL3, see LICENSE for more details.

"""

__title__ = 'spotifython'
__author__ = 'VAWVAW'
__license__ = 'GPL3'
__copyright__ = 'Copyright 2022-present VAWVAW'

# noinspection PyUnboundLocalVariable
__path__ = __import__('pkgutil').extend_path(__path__, __name__)

from collections import namedtuple
import logging

from .client import Client
from .authentication import Authentication
from .user import User
from .errors import SpotifyException, BadRequestException, InvalidTokenException, ForbiddenException, NotFoundException, NotModified, InternalServerError, InvalidTokenData, PayloadToLarge, HttpError
from .scope import Scope
from .playlist import Playlist
from .track import Track
from .uri import URI
from .album import Album
from .artist import Artist
from .episode import Episode
from .show import Show
from .me import Me, SavedTracks
from .abc import Playable, PlayContext, Cacheable

VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial')

version_info = VersionInfo(major=0, minor=2, micro=3, releaselevel='development', serial=0)
__version__ = '0.2.3'

logging.getLogger(__name__).addHandler(logging.NullHandler())
