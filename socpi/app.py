import logging
import asyncio
from asyncio.streams import StreamReader, StreamWriter
from inspect import isasyncgenfunction, isgeneratorfunction
from types import GeneratorType
from typing import Tuple

from .request import request_repr

from .request import Request
from .utils import decode, encode
from .message import Message, MessageType

logger = logging.getLogger(__name__)


async def handle_generator(reader: StreamReader, writer: StreamWriter, iter):
    if reader.at_eof():
        raise EOFError("EOF read")
    message = decode(await reader.readline())
    if message.type != MessageType.generator_request:
        raise Exception("Invaild message recived")
    writer.write(encode(Message(MessageType.generator_result, iter)))
    await writer.drain()


class App:
    def __init__(self, host: str | Tuple[str, int]) -> None:
        self.endpoints = {}
        self._host = host

    async def _handleConnection(
        self, reader: StreamReader, writer: StreamWriter
    ):
        try:
            request = decode(await reader.readline())
            if not isinstance(request, Request):
                raise Exception("Failed to cast")
        except Exception as e:
            logger.error(f"Bad Request < {e} />")
            writer.write(encode(Message(MessageType.exception, e)))
            writer.write_eof()
            await writer.drain()
            return

        logger.info(f"Connection to {request_repr(request)}")
        try:
            endpoint = self.endpoints[request.endpoint]
            result = endpoint(*request.args, **request.kwargs)
            if isgeneratorfunction(self.endpoints[request.endpoint]):
                logger.debug(
                    f"Handling Generator result at {request_repr(request)}"
                )
                for iter in result:
                    logger.debug(
                        f"\tHandling Generator result {iter.__repr__()} at {request_repr(request)}"
                    )
                    await handle_generator(reader, writer, iter)
                return
            elif isasyncgenfunction(self.endpoints[request.endpoint]):
                logger.debug(
                    f"Handling Generator result at {request_repr(request)}"
                )
                async for iter in result:
                    logger.debug(
                        f"\tHandling Generator result {iter.__repr__()} at {request_repr(request)}"
                    )
                    await handle_generator(reader, writer, iter)
                return
            elif asyncio.iscoroutine(result):
                result = await result

            writer.write(encode(Message(MessageType.function_result, result)))
        except Exception as e:
            logger.error(f"Exception at endpoint {request_repr(request)}: {e}")
            writer.write(encode(Message(MessageType.exception, e)))
        finally:
            writer.write_eof()
            await writer.drain()

    def register(self, f):
        self.endpoints[f.__name__] = f
        return f

    async def _server_factory(self):
        if isinstance(self._host, tuple):
            host, port = self._host
            logger.info(f"Starting server at {host}:{port}")
            return await asyncio.start_server(
                host=host, port=port, client_connected_cb=self._handleConnection
            )
        else:
            logger.info(f"Starting server at {self._host}")
            return await asyncio.start_unix_server(
                path=self._host, client_connected_cb=self._handleConnection
            )

    async def run(self):
        server = await self._server_factory()
        async with server:
            await server.serve_forever()
