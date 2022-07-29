import base64
import pickle


def encode(obj):
    return base64.b64encode(pickle.dumps(obj)) + b'\n'

def decode(data: bytes):
    return pickle.loads(base64.b64decode(data))
