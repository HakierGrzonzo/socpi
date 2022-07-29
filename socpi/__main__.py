from socpi.client import Client
from .app import App
from socpi import get_path_in_run
import asyncio
import logging


logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="A pickled socket library"
    )
    parser.add_argument("mode", type=str)
    args = parser.parse_args()

    app = App(get_path_in_run('test'))
    
    @app.register
    def foo(arg: str):
        return arg

    loop = asyncio.get_event_loop()
    if args.mode == "client":
        client = Client(app)
        async def test():
            out = await client.foo('test')
            print(out)
        loop.run_until_complete(test())
    elif args.mode == "server":
        loop.run_until_complete(app.run())
