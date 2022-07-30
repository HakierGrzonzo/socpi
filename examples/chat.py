from socpi import App, Client, get_path_in_run
from collections import defaultdict
import argparse
import aiofiles
import asyncio

app = App(("0.0.0.0", 9999))

messages = defaultdict(lambda: asyncio.Queue())


@app.register
async def post_message(message: str, sender: str):
    """Send message to all clients that the server knows off."""
    await asyncio.gather(
        *list(
            queue.put(f"<{sender}> {message.strip()}")
            for user, queue in messages.items()
            if user != sender
        )
    )


@app.register
async def consume(user: str):
    """
    Returns messages as they come in and also returns any messages that
    weren't recived
    """
    queue = messages[user]
    while True:
        msg = await queue.get()
        yield msg


client = Client(app)


async def print_new_messages(user: str):
    """Prints the messages to stdout as they come in"""
    async for msg in client.consume(user):
        print(msg)


async def get_input(sender: str):
    """Reads stdin and sends messages when a newline is entered"""
    async with aiofiles.open("/dev/stdin") as stdin:
        async for line in stdin:
            if line.strip() == "exit":
                return
            try:
                await client.post_message(line, sender)
            except Exception as e:
                print(e)


async def main(sender: str):
    t = asyncio.create_task(print_new_messages(sender))
    await get_input(sender)
    t.cancel()


parser = argparse.ArgumentParser(description="A pickled socket chat")
parser.add_argument("mode", type=str)
parser.add_argument("--user", type=str, required=False)
args = parser.parse_args()
if args.mode == "server":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(app.run())
else:
    asyncio.run(main(args.user))
