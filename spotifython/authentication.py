from .scope import Scope


class Authentication:
    """
    Store the data needed to interact with the Spotify API. Not all arguments are needed. Options are (client_id, client_secret, scope), (client_id, client_secret, scope, refresh_token), (token, token_expires)

    :param client_id: the Client ID of the application
    :param client_secret: the Client Secret of the application (click on "SHOW CLIENT SECRET")
    :param scope: the Scope object or string reflecting the permissions you need
    :param show_dialog: whether to query the user every time a new refresh token is requested
    :param token_expires: timestamp when the token expires
    """

    def __init__(self, client_id: str = None, client_secret: str = None, scope: (Scope | str) = None, show_dialog: bool = False, refresh_token: str = None, token: str = None, token_expires: float = 0.0):
        assert isinstance(client_id, str)
        assert isinstance(client_secret, str)
        assert isinstance(scope, (Scope | str | None))
        assert isinstance(refresh_token, (str | None))
        assert isinstance(token, (str | None))
        assert isinstance(token_expires, float)
        assert isinstance(show_dialog, bool)

        self.token = token
        self.token_expires = token_expires
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.show_dialog = show_dialog
        self.scope = str(scope)

    def to_dict(self) -> dict:
        """
        Call this function before exiting and store the data somewhere safe.

        :return: dict with organised data for caching
        """
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
            "show_dialog": self.show_dialog,
            "refresh_token": self.refresh_token,
            "token": self.token,
            "token_expires": self.token_expires
        }

    @classmethod
    def from_dict(cls, data: dict):
        """
        :param data: dict generated in `to_dict()`
        :return: Authentication
        """
        return cls(
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            scope=data["scope"],
            show_dialog=data["show_dialog"],
            refresh_token=data["refresh_token"],
            token=data["token"],
            token_expires=data["token_expires"]
        )
