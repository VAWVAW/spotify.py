from .user import User
from .playlist import Playlist
from .episode import Episode
from .track import Track
from .artist import Artist
from .album import Album
from .show import Show

datatypes = {
    "playlist": Playlist,
    "episode": Episode,
    "track": Track,
    "album": Album,
    "artist": Artist,
    "show": Show,
    "user": User
}

