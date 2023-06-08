from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

if TYPE_CHECKING:
    from pykka import Future


T = TypeVar("T")


class Envelope(Generic[T]):
    """Envelope to add metadata to a message.

    This is an internal type and is not part of the public API.

    :param message: the message to send
    :type message: any
    :param reply_to: the future to reply to if there is a response
    :type reply_to: :class:`pykka.Future`
    """

    # Using slots speeds up envelope creation with ~20%
    __slots__ = ["message", "reply_to"]

    message: T
    reply_to: Optional[Future[Any]]

    def __init__(self, message: T, reply_to: Optional[Future[Any]] = None) -> None:
        self.message = message
        self.reply_to = reply_to

    def __repr__(self) -> str:
        return f"Envelope(message={self.message!r}, reply_to={self.reply_to!r})"
