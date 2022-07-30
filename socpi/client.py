from typing import Callable, Tuple
from inspect import isasyncgenfunction, isgeneratorfunction
import asyncio

from .message import Message, MessageType

from .request import Request, request_repr
from .utils import encode, decode
from .app import App

import logging

logger = logging.getLogger(__name__)


class Client:
    def __init__(self, app: App) -> None:
        self.__host = app._host
        self.__endpoints = app.endpoints

    async def _connection_factory(
        self,
    ) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        if isinstance(self.__host, tuple):
            host, port = self.__host
            return await asyncio.open_connection(host=host, port=port)
        else:
            return await asyncio.open_unix_connection(self.__host)

    async def _start_request(self, name, args, kwargs):
        """
        Starts a conversation with the server and passes the parameters
        for it to call the remote procedure
        """
        request = Request(name, *args, **kwargs)
        reader, writer = await self._connection_factory()
        # Write the request object to initiate the conversation
        writer.write(encode(request))
        await writer.drain()
        logger.debug(f"Connected to {request_repr(request)}")
        return reader, writer

    def __getattr__(self, __name: str) -> Callable:
        """
        Returns an async function or an async generator that connects and
        recives the data from the server.
        """
        if not __name in self.__endpoints.keys():
            raise Exception("No such endpoint!")

        if isasyncgenfunction(self.__endpoints[__name]) or isgeneratorfunction(
            self.__endpoints[__name]
        ):
            # If the target function on the backend is a generator, we need a
            # special handler

            async def handler_generator(*args, **kwargs):
                reader, writer = await self._start_request(__name, args, kwargs)
                # generators return data on demand
                try:
                    # tell the backend that we are ready to recive a new
                    # message
                    writer.write(
                        encode(Message(MessageType.generator_request, None))
                    )
                    await writer.drain()
                    async for line in reader:
                        msg = decode(line)
                        # Handle exceptions embeded in diffrent types of
                        # messages
                        match msg.type:
                            case MessageType.exception:
                                raise msg.content
                            case MessageType.generator_result:
                                yield msg.content
                            case other:
                                raise Exception("Unknown answer")
                        # we have yielded the message, now it is time to handle
                        # another one
                        writer.write(
                            encode(Message(MessageType.generator_request, None))
                        )
                        await writer.drain()
                finally:
                    writer.write_eof()
                    await writer.drain()

            handler_generator.__annotations__ = self.__endpoints[
                __name
            ].__annotations__
            handler_generator.__name__ = __name
            handler_generator.__qualname__ = __name
            return handler_generator
        else:
            # handle normal functions

            async def handler(*args, **kwargs):
                reader, writer = await self._start_request(__name, args, kwargs)
                # normal functions only return one thing
                msg = decode(await reader.readline())
                try:
                    # Handle exceptions embeded in diffrent types of
                    # messages
                    match msg.type:
                        case MessageType.function_result:
                            return msg.content
                        case MessageType.exception:
                            raise msg.content
                        case other:
                            raise Exception("Unknown answer")
                finally:
                    writer.write_eof()
                    await writer.drain()

            handler.__annotations__ = self.__endpoints[__name].__annotations__
            handler.__name__ = __name
            handler.__qualname__ = __name
            return handler
