from .app import App
import os

def get_path_in_run(name: str) -> str:
    uid = os.getuid()
    return os.path.join("/run", "user", str(uid), name)

