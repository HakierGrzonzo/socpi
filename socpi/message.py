from enum import Enum


class MessageType(Enum):
    """
    Specifies what is the content of the message:
        - exception - an Exception to be raised
        - generator_result - a value yielded by a generator
        - generator_request - an empty message as an request for another 
                              value from the generator
        - function_result - a value to be returned
    """
    exception = 1
    generator_result = 2
    generator_request = 3
    function_result = 4


class Message:
    """
    Caries the data with some metadata to describe what should be done with it
    """
    def __init__(self, type: MessageType, content) -> None:
        self.type = type
        self.content = content
