class SpotifyException(Exception):
    """
    base class for Exceptions from this library
    """


class BadRequestException(SpotifyException):
    """
    corresponds to a 400 error from the Spotify API
    """


class InvalidTokenException(SpotifyException):
    """
    corresponds to a 401 error from the Spotify API
    """


class ForbiddenException(SpotifyException):
    """
    corresponds to a 403 error from the Spotify API
    """


class NotFoundException(SpotifyException):
    """
    corresponds to a 404 error from the Spotify API
    """


class NotModified(SpotifyException):
    """
    corresponds to a 304 error from the Spotify API
    """


class InternalServerError(SpotifyException):
    """
    corresponds to a 500 error from the Spotify API
    """


class InvalidTokenData(SpotifyException):
    pass


class Retry(Exception):
    pass


class ElementOutdated(Exception):
    pass

