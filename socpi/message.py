from enum import Enum


class MessageType(Enum):
    exception = 1
    generator_result = 2
    generator_request = 3
    function_result = 4


class Message:
    def __init__(self, type: MessageType, content) -> None:
        self.type = type
        self.content = content
