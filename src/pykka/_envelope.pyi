from typing import Any, Optional, Union

from pykka import Future

class Envelope:
    message: Any
    reply_to: Optional[Future]
    timestamp: float
    def __init__(
        self,
        message: Any,
        reply_to: Optional[Future] = ...,
        delay: Union[float, int] = ...,
    ) -> None: ...
    def __repr__(self) -> str: ...
