import requests
import base64
import time
import logging

from .errors import NotModified, BadRequestException, InvalidTokenException, ForbiddenException, NotFoundException, Retry, InternalServerError, InvalidTokenData, PayloadToLarge, HttpError
from .authentication import Authentication
from .scope import Scope

log = logging.getLogger(__name__)


class Connection:
    def __init__(self, authentication: Authentication):
        self._authentication = authentication

    def _get_header(self) -> dict:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization":
                "Bearer " + self._authentication.token
        }

    def _evaluate_response(self, response: requests.Response) -> dict | None:
        match response.status_code:
            case 202:
                # Accepted (seems to imply success and 204)
                return None
            case 204:
                # no content
                return None
            case 304:
                raise NotModified(response.text)
            case 400:
                raise BadRequestException(response.text)
            case 401:
                if self.is_expired:
                    self._get_token()
                    raise Retry()
                raise InvalidTokenException(response.text)
            case 403:
                raise ForbiddenException(response.text)
            case 404:
                raise NotFoundException(response.text)
            case 413:
                raise PayloadToLarge(response.text)
            case 429:
                # rate limit
                log.warning("rate limit exceeded; will retry in 5 seconds")
                time.sleep(5)
                raise Retry()
            case 500:
                raise InternalServerError(response.text)
            case 503:
                # service unavailable
                log.warning("service unavailable; will retry in 1 second")
                time.sleep(1)
                raise Retry()
            case x:
                if x >= 300:
                    raise HttpError((x, response.text))
                if x < 200:
                    time.sleep(1)
                    raise Retry()

        try:
            return response.json()
        except requests.JSONDecodeError:
            return None

    def make_request(self, method: str, endpoint: str, data: str = None) -> dict | None:
        url = "https://api.spotify.com/v1/" + endpoint
        if self._authentication.token is None:
            self._get_token()
        if data is not None:
            log.debug("%s %s with %s", method, url, data)
        retries = 5
        while retries > 0:
            response = requests.request(method, url, data=data, headers=self._get_header())
            try:
                data = self._evaluate_response(response)
            except Retry:
                retries -= 1
                log.info("retrying (%d)", retries)
            else:
                break
        else:
            log.error("request ran out of retries")
        return data

    @staticmethod
    def add_parameters_to_endpoint(endpoint: str, **params) -> str:
        param_strings = []
        for key in params.keys():
            if params[key] is None:
                continue
            param_strings.append(str(key) + "=" + str(params[key]))

        if len(param_strings) == 0:
            return endpoint

        endpoint += "?"
        endpoint += "&".join(param_strings)
        return endpoint

    def _request_token(self):
        """
        :return: {'token_type': 'Bearer', 'scope': scope_str, 'refresh_token': refresh_token}
        """
        if self._authentication.client_id is None or self._authentication.client_secret is None:
            raise InvalidTokenData("client_id and client_secret are needed to request access and refresh token")
        if self._authentication.scope == 'None':
            raise InvalidTokenData("a scope is needed to request access and refresh token")

        import random
        import string
        import webbrowser
        import socket

        # generate random string to secure against request forgery
        state = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
        # redirect uri that needs to be set in the application settings
        redirect_uri = "http://localhost:2342/"

        # spotify query that the user needs to accept to gain the access token
        endpoint = self.add_parameters_to_endpoint(
            "https://accounts.spotify.com/authorize",
            client_id=self._authentication.client_id,
            response_type="code",
            scope=str(self._authentication.scope),
            state=state,
            show_dialog=self._authentication.show_dialog,
            redirect_uri=redirect_uri
        )
        # open the url in the (hopefully) default browser
        webbrowser.open(endpoint)
        print("Please check your web browser for identification.")

        # simple function to listen for and extract the http query from one request
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        serversocket.bind(("localhost", 2342))
        serversocket.listen()

        # wait for connection
        (clientsocket, addr) = serversocket.accept()
        data = str(clientsocket.recv(1024), "utf8")
        clientsocket.send(bytes("You can close this page now.", "utf8"))
        clientsocket.close()
        serversocket.close()

        # extract query from request
        query_str = data.split("\n")[0].split(" ")[1].split("?")[1].split("&")
        query = {}
        for argument in query_str:
            q = argument.split("=")
            query[q[0]] = q[1]

        # simple error management
        if query["state"] != state:
            raise Exception("transmission changed unexpectedly")

        if "code" not in query.keys():
            raise Exception(query["error"])

        auth_code = query["code"]

        # make request to spotify to get a Bearer from the basic token
        form = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": redirect_uri,
        }

        encoded = base64.b64encode(bytes(self._authentication.client_id + ":" + self._authentication.client_secret, "utf8")).decode("utf8")

        header = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + encoded
        }

        response = requests.post("https://accounts.spotify.com/api/token", data=form, headers=header)
        data = response.json()

        if data["token_type"] != "Bearer":
            raise Exception("received invalid token")

        self._authentication.token = data["access_token"]
        self._authentication.token_expires = time.time() + data["expires_in"]
        self._authentication.refresh_token = data["refresh_token"]

        self._authentication.scope = data["scope"]

    def _refresh_access_token(self):
        """
        make request to spotify to get a new Bearer from the refresh token
        :return: {'scope': scope_str}
        """
        if self._authentication.client_id is None or self._authentication.client_secret is None:
            raise InvalidTokenData("client_id and client_secret are needed to refresh the access token")
        if self._authentication.scope == 'None':
            raise InvalidTokenData("a scope is needed to refresh the access token")

        form = {
            "grant_type": "refresh_token",
            "refresh_token": self._authentication.refresh_token
        }

        encoded = base64.b64encode(bytes(self._authentication.client_id + ":" + self._authentication.client_secret, "utf8")).decode("utf8")

        header = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + encoded
        }

        response = requests.post("https://accounts.spotify.com/api/token", data=form, headers=header)
        data = response.json()

        if "error" in data.keys():
            raise Exception(data["error"] + ": " + data["error_description"])

        if data["token_type"] != "Bearer":
            raise Exception("received invalid token")

        self._authentication.token = data["access_token"]
        self._authentication.token_expires = time.time() + data["expires_in"]

        if not Scope.contains(data["scope"], self._authentication.scope):
            return self._request_token()
        self._authentication.scope = data["scope"]

    def _get_token(self):
        if self._authentication.refresh_token is not None:
            log.info("refreshing access token")
            self._refresh_access_token()
        else:
            log.info("requesting access and refresh token")
            self._request_token()

    def dump_token_data(self) -> dict:
        return {
            "client_id": self._authentication.client_id,
            "client_secret": self._authentication.client_secret,
            "scope": str(self._authentication.scope),
            "refresh_token": self._authentication.refresh_token,
            "show_dialog": self._authentication.show_dialog,
            "token": self._authentication.token,
            "expires": self._authentication.token_expires
        }

    @property
    def is_expired(self) -> bool:
        return self._authentication.token_expires < time.time()
