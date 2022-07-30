import base64
import pickle
import os


def encode(obj):
    return base64.b64encode(pickle.dumps(obj)) + b"\n"


def decode(data: bytes):
    return pickle.loads(base64.b64decode(data))


def get_path_in_run(name: str) -> str:
    uid = os.getuid()
    return os.path.join("/run", "user", str(uid), name)
