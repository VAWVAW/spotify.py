import aiohttp
import asyncio
import json
import base64
import time

from .errors import NotModified, BadRequestException, InvalidTokenException, ForbiddenException, NotFoundException, Retry, InternalServerError
from .scope import Scope


class Connection:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self._token = None
        self._expires = 0
        self._client_id = None
        self._client_secret = None
        self._refresh_token = None
        self._show_dialog = False
        self._scope = ""

    def _get_header(self) -> dict:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization":
                "Bearer " + self._token
        }

    async def _evaluate_response(self, response: aiohttp.ClientResponse) -> dict | None:
        match response.status:
            case 204:
                # no content
                return None
            case 304:
                raise NotModified(await response.text())
            case 400:
                raise BadRequestException(json.loads(await response.text()))
            case 401:
                if self.is_expired:
                    await self._get_token()
                    raise Retry()
                raise InvalidTokenException(json.loads(await response.text()))
            case 403:
                raise ForbiddenException(json.loads(await response.text()))
            case 404:
                raise NotFoundException(json.loads(await response.text()))
            case 429:
                # rate limit
                await asyncio.sleep(5)
                raise Retry()
            case 500:
                raise InternalServerError(await response.text())
            case 503:
                # service unavailable
                await asyncio.sleep(1)
                raise Retry()

        try:
            return json.loads(await response.text())
        except json.decoder.JSONDecodeError:
            return None

    async def make_request(self, method: str, endpoint: str, data: str = None) -> dict | None:
        url = "https://api.spotify.com/v1/" + endpoint
        if self._token is None:
            await self._get_token()
        response = await self.session.request(method, url, data=data, headers=self._get_header())
        try:
            data = await self._evaluate_response(response)
        except Retry:
            data = await self._evaluate_response(await self.session.request(method, url, data=data, headers=self._get_header()))
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

    async def close(self):
        await self.session.close()

    async def _request_token(self) -> dict:
        """
        :return: {'token_type': 'Bearer', 'scope': scope_str, 'refresh_token': refresh_token}
        """
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
            client_id=self._client_id,
            response_type="code",
            scope=str(self._scope),
            state=state,
            show_dialog=self._show_dialog,
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
        form = aiohttp.FormData()
        form.add_field("grant_type", "authorization_code")
        form.add_field("code", auth_code)
        form.add_field("redirect_uri", redirect_uri)

        encoded = base64.b64encode(bytes(self._client_id + ":" + self._client_secret, "utf8")).decode("utf8")

        header = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + encoded
        }

        response = await self.session.request("POST", "https://accounts.spotify.com/api/token", data=form, headers=header)
        data = json.loads(await response.text())

        if data["token_type"] != "Bearer":
            raise Exception("received invalid token")

        self._token = data["access_token"]
        self._expires = time.time() + data["expires_in"]
        self._refresh_token = data["refresh_token"]

        return {"scope": data["scope"], "refresh_token": data["refresh_token"]}

    async def _refresh_access_token(self) -> dict:
        """
        make request to spotify to get a new Bearer from the refresh token
        :return: {'scope': scope_str}
        """

        form = aiohttp.FormData()
        form.add_field("grant_type", "refresh_token")
        form.add_field("refresh_token", self._refresh_token)

        encoded = base64.b64encode(bytes(self._client_id + ":" + self._client_secret, "utf8")).decode("utf8")

        header = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + encoded
        }

        response = await self.session.request("POST", "https://accounts.spotify.com/api/token", data=form, headers=header)
        data = json.loads(await response.text())

        if data["token_type"] != "Bearer":
            raise Exception("received invalid token")

        self._token = data["access_token"]
        self._expires = time.time() + data["expires_in"]

        return {"scope": data["scope"]}

    async def _get_token(self):
        if self._refresh_token is not None:
            await self._refresh_access_token()
        else:
            await self._request_token()

    def set_token_data(self, client_id: str, client_secret: str, scope: Scope = Scope(), refresh_token: str = None, show_dialog: bool = False, token: str = None, expires: int = 0):
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._refresh_token = refresh_token
        self._show_dialog = show_dialog
        self._token = token
        self._expires = expires

    def dump_token_data(self) -> dict:
        return {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": str(self._scope),
            "refresh_token": self._refresh_token,
            "show_dialog": self._show_dialog,
            "token": self._token,
            "expires": self._expires
        }

    @property
    def is_expired(self) -> bool:
        return self._expires < time.time()
