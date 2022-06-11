class SpotifyException(Exception):
    pass


class BadRequestException(SpotifyException):
    pass


class InvalidTokenException(SpotifyException):
    pass


class ForbiddenException(SpotifyException):
    pass


class NotFoundException(SpotifyException):
    pass


class NotModified(SpotifyException):
    pass


class InternalServerError(SpotifyException):
    pass


class Retry(Exception):
    pass


class ElementOutdated(Exception):
    pass


class InvalidTokenData(Exception):
    pass
