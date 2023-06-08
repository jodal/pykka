from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Literal,
    Optional,
    TypeVar,
    Union,
    overload,
)

from pykka import ActorDeadError, ActorProxy
from pykka._envelope import Envelope
from pykka.messages import _ActorStop

if TYPE_CHECKING:
    from threading import Event

    from pykka import Actor, Future
    from pykka._actor import ActorInbox

__all__ = ["ActorRef"]


A = TypeVar("A", bound="Actor")


class ActorRef(Generic[A]):
    """Reference to a running actor which may safely be passed around.

    :class:`ActorRef` instances are returned by :meth:`Actor.start` and the
    lookup methods in :class:`ActorRegistry <pykka.ActorRegistry>`. You should
    never need to create :class:`ActorRef` instances yourself.

    :param actor: the actor to wrap
    :type actor: :class:`Actor`
    """

    #: The class of the referenced actor.
    actor_class: type[A]

    #: See :attr:`Actor.actor_urn`.
    actor_urn: str

    #: See :attr:`Actor.actor_inbox`.
    actor_inbox: ActorInbox

    #: See :attr:`Actor.actor_stopped`.
    actor_stopped: Event

    def __init__(
        self: ActorRef[A],
        actor: A,
    ) -> None:
        self._actor = actor
        self.actor_class = actor.__class__
        self.actor_urn = actor.actor_urn
        self.actor_inbox = actor.actor_inbox
        self.actor_stopped = actor.actor_stopped

    def __repr__(self) -> str:
        return f"<ActorRef for {self}>"

    def __str__(self) -> str:
        return f"{self.actor_class.__name__} ({self.actor_urn})"

    def is_alive(self) -> bool:
        """Check if actor is alive.

        This is based on the actor's stopped flag. The actor is not guaranteed
        to be alive and responding even though :meth:`is_alive` returns
        :class:`True`.

        :return:
            Returns :class:`True` if actor is alive, :class:`False` otherwise.
        """
        return not self.actor_stopped.is_set()

    def tell(
        self,
        message: Any,
    ) -> None:
        """Send message to actor without waiting for any response.

        Will generally not block, but if the underlying queue is full it will
        block until a free slot is available.

        :param message: message to send
        :type message: any

        :raise: :exc:`pykka.ActorDeadError` if actor is not available
        :return: nothing
        """
        if not self.is_alive():
            raise ActorDeadError(f"{self} not found")
        self.actor_inbox.put(Envelope(message))

    @overload
    def ask(
        self,
        message: Any,
        *,
        block: Literal[False],
        timeout: Optional[float] = None,
    ) -> Future[Any]:
        ...

    @overload
    def ask(
        self,
        message: Any,
        *,
        block: Literal[True],
        timeout: Optional[float] = None,
    ) -> Any:
        ...

    @overload
    def ask(
        self,
        message: Any,
        *,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> Union[Any, Future[Any]]:
        ...

    def ask(
        self,
        message: Any,
        *,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> Union[Any, Future[Any]]:
        """Send message to actor and wait for the reply.

        The message can be of any type.
        If ``block`` is :class:`False`, it will immediately return a
        :class:`Future <pykka.Future>` instead of blocking.

        If ``block`` is :class:`True`, and ``timeout`` is :class:`None`, as
        default, the method will block until it gets a reply, potentially
        forever. If ``timeout`` is an integer or float, the method will wait
        for a reply for ``timeout`` seconds, and then raise
        :exc:`pykka.Timeout`.

        :param message: message to send
        :type message: any

        :param block: whether to block while waiting for a reply
        :type block: boolean

        :param timeout: seconds to wait before timeout if blocking
        :type timeout: float or :class:`None`

        :raise: :exc:`pykka.Timeout` if timeout is reached if blocking
        :raise: any exception returned by the receiving actor if blocking
        :return: :class:`pykka.Future`, or response if blocking
        """
        future = self.actor_class._create_future()  # noqa: SLF001

        try:
            if not self.is_alive():
                raise ActorDeadError(f"{self} not found")  # noqa: TRY301
        except ActorDeadError:
            future.set_exception()
        else:
            self.actor_inbox.put(Envelope(message, reply_to=future))

        if block:
            return future.get(timeout=timeout)

        return future

    @overload
    def stop(
        self,
        *,
        block: Literal[True],
        timeout: Optional[float] = None,
    ) -> bool:
        ...

    @overload
    def stop(
        self,
        *,
        block: Literal[False],
        timeout: Optional[float] = None,
    ) -> Future[bool]:
        ...

    @overload
    def stop(
        self,
        *,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> Union[Any, Future[Any]]:
        ...

    def stop(
        self,
        *,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> Union[Any, Future[Any]]:
        """Send a message to the actor, asking it to stop.

        Returns :class:`True` if actor is stopped or was being stopped at the
        time of the call. :class:`False` if actor was already dead. If
        ``block`` is :class:`False`, it returns a future wrapping the result.

        Messages sent to the actor before the actor is asked to stop will
        be processed normally before it stops.

        Messages sent to the actor after the actor is asked to stop will
        be replied to with :exc:`pykka.ActorDeadError` after it stops.

        The actor may not be restarted.

        ``block`` and ``timeout`` works as for :meth:`ask`.

        :return: :class:`pykka.Future`, or a boolean result if blocking
        """
        ask_future = self.ask(_ActorStop(), block=False)

        def _stop_result_converter(timeout: Optional[float]) -> bool:
            try:
                ask_future.get(timeout=timeout)
            except ActorDeadError:
                return False
            else:
                return True

        converted_future = ask_future.__class__()
        converted_future.set_get_hook(_stop_result_converter)

        if block:
            return converted_future.get(timeout=timeout)

        return converted_future

    def proxy(self: ActorRef[A]) -> ActorProxy[A]:
        """Wrap the :class:`ActorRef` in an :class:`ActorProxy <pykka.ActorProxy>`.

        Using this method like this::

            proxy = AnActor.start().proxy()

        is analogous to::

            proxy = ActorProxy(AnActor.start())

        :raise: :exc:`pykka.ActorDeadError` if actor is not available
        :return: :class:`pykka.ActorProxy`
        """
        return ActorProxy(actor_ref=self)
