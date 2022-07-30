from socpi import App, Client, get_path_in_run
import asyncio
import logging


async def print_generator(gen, rep):
    """
    A utility function to print every value from an async generator
    """
    try:
        async for x in gen:
            print(rep, x)
            await asyncio.sleep(0.3)
    except Exception as e:
        print(f"Got exception {e} from {rep}")


logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    # import and setup an argument parser to decide if we are a server or 
    # a client
    import argparse

    parser = argparse.ArgumentParser(description="A pickled socket library")
    parser.add_argument("mode", type=str)
    args = parser.parse_args()

    # setup application as a unix server listening at a socket in
    # /run/$your_uid/test
    app = App(get_path_in_run("test"))

    # register endpoints for the application

    @app.register
    def foo(arg: str):
        """Just an echo function"""
        return arg

    @app.register
    async def bar():
        """A sleeping function"""
        print("hello from the other side")
        await asyncio.sleep(1)
        return "done"

    @app.register
    async def failer():
        """throw an exception"""
        raise Exception("foo")

    @app.register
    def generator(start, stop):
        """A sync generator"""
        yield from range(start, stop)

    @app.register
    async def async_generator():
        """An async generator with exceptions"""
        yield 1
        await asyncio.sleep(0.3)
        yield 2
        await asyncio.sleep(0.3)
        yield 3
        await asyncio.sleep(0.3)
        raise Exception("foo")

    if args.mode == "client":
        # if we are a client, setup some test function
        client = Client(app)

        async def test():
            """
            Calls all the methods on a server
            """
            print(
                await asyncio.gather(
                    client.foo("test"),
                    client.bar(),
                )
            )
            try:
                await client.failer()
            except Exception as e:
                print(e)

            # print values in generators with delays
            await asyncio.gather(
                print_generator(client.generator(0, 10), client.generator),
                print_generator(
                    client.async_generator(), client.async_generator
                ),
            )

        asyncio.run(test())
    elif args.mode == "server":
        # run server
        asyncio.run(app.run())
