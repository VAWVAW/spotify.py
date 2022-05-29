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
                    await self.refresh_access_token()
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

    # TODO concentrate in session.request()
    async def make_get_request(self, endpoint: str) -> dict | None:
        response = await self.session.get("https://api.spotify.com/v1/" + endpoint, headers=self._get_header())

        try:
            data = await self._evaluate_response(response)
        except Retry:
            data = await self.make_get_request(endpoint=endpoint)

        return data

    async def make_put_request(self, endpoint: str, data: str = None) -> dict | None:
        response = await self.session.put("https://api.spotify.com/v1/" + endpoint, data=data, headers=self._get_header())

        try:
            data = await self._evaluate_response(response)
        except Retry:
            data = await self.make_put_request(data=data, endpoint=endpoint)

        return data

    async def make_post_request(self, endpoint: str, data: str = None) -> dict | None:
        response = await self.session.post("https://api.spotify.com/v1/" + endpoint, data=data, headers=self._get_header())

        try:
            data = await self._evaluate_response(response)
        except Retry:
            data = await self.make_post_request(data=data, endpoint=endpoint)

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

    async def get_token(self, client_id: str, client_secret: str, scope: Scope = None, show_dialog: bool = False) -> dict:
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

        if scope is None:
            scope = ""

        # spotify query that the user needs to accept to gain the access token
        endpoint = self.add_parameters_to_endpoint(
            "https://accounts.spotify.com/authorize",
            client_id=client_id,
            response_type="code",
            scope=str(scope),
            state=state,
            show_dialog=show_dialog,
            redirect_uri=redirect_uri
        )
        # open the url in the (hopefully) default browser
        webbrowser.open(endpoint)

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

        encoded = base64.b64encode(bytes(client_id + ":" + client_secret, "utf8")).decode("utf8")

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
        self._client_id = client_id
        self._client_secret = client_secret

        return {"scope": data["scope"], "refresh_token": data["refresh_token"]}

    async def refresh_access_token(self, client_id: str = None, client_secret: str = None, refresh_token: str = None) -> dict:
        """
        make request to spotify to get a new Bearer from the refresh token
        :return: {'scope': scope_str}
        """
        # use cached data if needed
        if client_id is None:
            if self._client_id is None:
                raise Exception("No client id provided")
            client_id = self._client_id

        if client_secret is None:
            if self._client_secret is None:
                raise Exception("No client secret provided")
            client_secret = self._client_secret

        if refresh_token is None:
            if self._refresh_token is None:
                raise Exception("No refresh token provided")
            refresh_token = self._refresh_token

        form = aiohttp.FormData()
        form.add_field("grant_type", "refresh_token")
        form.add_field("refresh_token", refresh_token)

        encoded = base64.b64encode(bytes(client_id + ":" + client_secret, "utf8")).decode("utf8")

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
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token

        return {"scope": data["scope"]}

    @property
    def is_expired(self) -> bool:
        return self._expires < time.time()
