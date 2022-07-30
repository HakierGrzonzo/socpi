# socpi

A simple async socket framework for python supporting *tcp* and *unix* sockets.
Allows you to go beyond *json* by using *pickle*

## How to use it

```python
from socpi import App, Client


# create the app with the socket path for unix sockets
app = App('/run/socpi')

# or use [ip, port] tuple for tcp
# app = App(('0.0.0.0', 4238))

# Specify your endpoints
@app.register
def echo(msg: str) -> str:
    return msg.lower()

# then launch your server, change `SERVER` to false to launch a client
SERVER = True
if SERVER:
    asyncio.run(app.run())

# or launch a client:
async def main():
    # no openapi required, everything is generated from the `app`
    client = Client(app)
    print(await client.echo('fooo'))

if not SERVER:
    asyncio.run(main())
```

There is a demo of a chat application in the `examples` directory.

## What can it do:

### Generators:

You can write and call generators and async generators:

```python
@app.register
def foo():
    print('hello from the other side')
    yield 'foo'
```

And call them like you would expect:

```python
async for i in client.foo():
    print(i)
```

Every generator will be turned into an async one!

### Exceptions:

Exception handling is completely transparent, just `raise` and `except` them 
as usual.

```python
@app.register
def failer():
    raise Exception('foo')
```

Handle them as usual, the objects will not be changed (but missing server and
broken connections will add some extra ones):

```python
try:
    await client.failer()
except Exception as e:
    print(e) # foo
```

### Serialization:

Anything `pickle`able will work, as such `remote code execution` is not a bug,
it is a feature. Deploying `socpi` to the wider internet is not recommended.

A `json` only version might be a more secure, less capable option.

