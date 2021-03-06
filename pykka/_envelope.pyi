from typing import Any, Optional

from pykka import Future

class Envelope:
    message: Any
    reply_to: Optional[Future]
    def __init__(self, message: Any, reply_to: Optional[Future] = ...) -> None: ...
    def __repr__(self) -> str: ...
