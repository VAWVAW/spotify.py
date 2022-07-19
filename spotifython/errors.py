class SpotifyException(Exception):
    """
    base class for Exceptions from this library
    """


class HttpError(SpotifyException):
    """
    base class for Http Exceptions from this library
    """


class BadRequestException(HttpError):
    """
    corresponds to a 400 error from the Spotify API
    """


class InvalidTokenException(HttpError):
    """
    corresponds to a 401 error from the Spotify API
    """


class ForbiddenException(HttpError):
    """
    corresponds to a 403 error from the Spotify API
    """


class NotFoundException(HttpError):
    """
    corresponds to a 404 error from the Spotify API
    """


class PayloadToLarge(HttpError):
    """
    corresponds to a 413 error from the Spotify API
    """


class NotModified(HttpError):
    """
    corresponds to a 304 error from the Spotify API
    """


class InternalServerError(HttpError):
    """
    corresponds to a 500 error from the Spotify API
    """


class InvalidTokenData(SpotifyException):
    pass


class Retry(Exception):
    pass


class ElementOutdated(Exception):
    pass

