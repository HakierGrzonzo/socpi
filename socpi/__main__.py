from socpi import App, Client, get_path_in_run
import asyncio
import logging

async def print_generator(gen, rep):
    try:
        async for x in gen:
            print(rep, x)
            await asyncio.sleep(0.3)
    except Exception as e:
        print(f"Got exception {e} from {rep}")


logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="A pickled socket library")
    parser.add_argument("mode", type=str)
    args = parser.parse_args()

    app = App(get_path_in_run("test"))

    @app.register
    def foo(arg: str):
        """Just an echo function"""
        return arg

    @app.register
    async def bar():
        """A sleeping function"""
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
        client = Client(app)

        async def test():
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
                print_generator(client.async_generator(), client.async_generator),
            )

        asyncio.run(test())
    elif args.mode == "server":
        asyncio.run(app.run())
