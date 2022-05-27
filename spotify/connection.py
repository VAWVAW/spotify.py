from typing import Any

import aiohttp
import asyncio
import json

import errors


class Connection:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    def _set_token(self, token: str):
        self.token = token

    def _get_header(self) -> dict:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization":
                "Bearer " + self.token
        }

    @staticmethod
    async def _evaluate_response(response: aiohttp.ClientResponse) -> dict | None:
        match response.status:
            case 204:
                # no content
                return None
            case 304:
                raise errors.NotModified(await response.text())
            case 400:
                raise errors.BadRequestException(json.loads(await response.text()))
            case 401:
                raise errors.InvalidTokenException(json.loads(await response.text()))
            case 403:
                raise errors.ForbiddenException(json.loads(await response.text()))
            case 404:
                raise errors.NotFoundException(json.loads(await response.text()))
            case 429:
                # rate limit
                await asyncio.sleep(5)
                raise errors.Retry()
            case 500:
                raise errors.InternalServerError(await response.text())
            case 503:
                # service unavailable
                await asyncio.sleep(1)
                raise errors.Retry()

        try:
            return json.loads(await response.text())
        except json.decoder.JSONDecodeError:
            return None

    async def make_get_request(self, endpoint: str, **formats) -> dict | None:
        response = await self.session.get("https://api.spotify.com/v1/" + endpoint.format(**formats), headers=self._get_header())

        try:
            data = await self._evaluate_response(response)
        except errors.Retry:
            data = await self.make_get_request(endpoint=endpoint, **formats)

        return data

    async def make_put_request(self, endpoint: str, data: str = None, **formats) -> dict | None:
        response = await self.session.put("https://api.spotify.com/v1/" + endpoint.format(**formats), data=data, headers=self._get_header())

        try:
            data = await self._evaluate_response(response)
        except errors.Retry:
            data = await self.make_post_request(data=data, endpoint=endpoint, **formats)

        return data

    async def make_post_request(self, endpoint: str, data: str = None, **formats) -> dict | None:
        response = await self.session.post("https://api.spotify.com/v1/" + endpoint.format(**formats), data=data, headers=self._get_header())

        try:
            data = await self._evaluate_response(response)
        except errors.Retry:
            data = await self.make_post_request(data=data, endpoint=endpoint, **formats)

        return data

    @staticmethod
    def add_parametrs_to_endpoint(endpoint: str, **params) -> str:
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

