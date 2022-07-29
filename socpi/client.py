from typing import Callable
import asyncio

from .request import Request
from .utils import encode, decode
from .app import App


class Client:
    def __init__(self, app: App) -> None:
        self.__path = app._path
        self.__endpoints = app.endpoints

    def __getattr__(self, __name: str) -> Callable:
        if not __name in self.__endpoints.keys():
            raise Exception("No such endpoint!")

        async def handler(*args, **kwargs):
            request = Request(__name, *args, **kwargs)
            reader, writer = await asyncio.open_unix_connection(self.__path)
            writer.write(encode(request))
            await writer.drain()
            return decode(await reader.readline())

        handler.__annotations__ = self.__endpoints[__name].__annotations__

        return handler
            
