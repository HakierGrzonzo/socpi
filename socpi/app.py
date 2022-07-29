import logging
import asyncio
from asyncio.streams import StreamReader, StreamWriter

from socpi.request import request_repr

from .request import Request
from .utils import decode, encode


class App:
    def __init__(self, path: str) -> None:
        self.endpoints = {}
        self._path = path

    async def _handleConnection(self, reader: StreamReader, writer: StreamWriter):
        try:
            request = decode(await reader.readline())
            if not isinstance(request, Request):
                raise Exception("Failed to cast")
            logging.info(f"Connection to {request_repr(request)}")
            endpoint = self.endpoints[request.endpoint]
            result = endpoint(*request.args, **request.kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            writer.write(encode(result))
            writer.write_eof()
            await writer.drain()
        except Exception as e:
            logging.error(f"Bad Connection < {e} />")
            raise e
    
    def register(self, f):
        self.endpoints[f.__name__] = f

    async def run(self):
        server = await asyncio.start_unix_server(self._handleConnection, path=self._path)
        logging.info("Starting server")
        async with server:
            await server.serve_forever()
