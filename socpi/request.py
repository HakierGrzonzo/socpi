class Request:
    def __init__(self, endpoint: str, *args, **kwargs) -> None:
        self.endpoint = endpoint
        self.args = args
        self.kwargs = kwargs


def request_repr(request: Request) -> str:
    return f"@{request.endpoint} - {request.args} - {request.kwargs}"
