from typing import Any

from pykka import Future

class Envelope:
    message: Any
    reply_to: Future | None
    def __init__(self, message: Any, reply_to: Future | None = ...) -> None: ...
