import logging
import asyncio
from asyncio.streams import StreamReader, StreamWriter
from inspect import isasyncgenfunction, isgeneratorfunction
from types import GeneratorType

from .request import request_repr

from .request import Request
from .utils import decode, encode
from .message import Message, MessageType

logger = logging.getLogger(__name__)


class App:
    def __init__(self, path: str) -> None:
        self.endpoints = {}
        self._path = path

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
                    writer.write(
                        encode(Message(MessageType.generator_result, iter))
                    )
                    logger.debug(
                        f"\tHandling Generator result {iter} at {request_repr(request)}"
                    )
                    await writer.drain()
                    message = decode(await reader.readline())
                    if message.type != MessageType.generator_request:
                        raise Exception("Invaild message recived")
                return
            elif isasyncgenfunction(self.endpoints[request.endpoint]):
                logger.debug(
                    f"Handling Generator result at {request_repr(request)}"
                )
                async for iter in result:
                    writer.write(
                        encode(Message(MessageType.generator_result, iter))
                    )
                    logger.debug(
                        f"\tHandling Generator result {iter} at {request_repr(request)}"
                    )
                    await writer.drain()
                    message = decode(await reader.readline())
                    if message.type != MessageType.generator_request:
                        raise Exception("Invaild message recived")
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

    async def run(self):
        server = await asyncio.start_unix_server(
            self._handleConnection, path=self._path
        )
        logger.info(f"Starting server at {self._path}")
        async with server:
            await server.serve_forever()
