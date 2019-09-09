from pykka import ActorDeadError, ActorProxy
from pykka._envelope import Envelope
from pykka.messages import _ActorStop


__all__ = ['ActorRef']


class ActorRef(object):
    """
    Reference to a running actor which may safely be passed around.

    :class:`ActorRef` instances are returned by :meth:`Actor.start` and the
    lookup methods in :class:`ActorRegistry <pykka.ActorRegistry>`. You should
    never need to create :class:`ActorRef` instances yourself.

    :param actor: the actor to wrap
    :type actor: :class:`Actor`
    """

    #: The class of the referenced actor.
    actor_class = None

    #: See :attr:`Actor.actor_urn`.
    actor_urn = None

    #: See :attr:`Actor.actor_inbox`.
    actor_inbox = None

    #: See :attr:`Actor.actor_stopped`.
    actor_stopped = None

    def __init__(self, actor):
        self._actor = actor
        self.actor_class = actor.__class__
        self.actor_urn = actor.actor_urn
        self.actor_inbox = actor.actor_inbox
        self.actor_stopped = actor.actor_stopped

    def __repr__(self):
        return '<ActorRef for {}>'.format(self)

    def __str__(self):
        return '{} ({})'.format(self.actor_class.__name__, self.actor_urn)

    def is_alive(self):
        """
        Check if actor is alive.

        This is based on the actor's stopped flag. The actor is not guaranteed
        to be alive and responding even though :meth:`is_alive` returns
        :class:`True`.

        :return:
            Returns :class:`True` if actor is alive, :class:`False` otherwise.
        """
        return not self.actor_stopped.is_set()

    def tell(self, message):
        """
        Send message to actor without waiting for any response.

        Will generally not block, but if the underlying queue is full it will
        block until a free slot is available.

        :param message: message to send
        :type message: any

        :raise: :exc:`pykka.ActorDeadError` if actor is not available
        :return: nothing
        """
        if not self.is_alive():
            raise ActorDeadError('{} not found'.format(self))
        self.actor_inbox.put(Envelope(message))

    def ask(self, message, block=True, timeout=None):
        """
        Send message to actor and wait for the reply.

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
        future = self.actor_class._create_future()

        try:
            if not self.is_alive():
                raise ActorDeadError('{} not found'.format(self))
        except ActorDeadError:
            future.set_exception()
        else:
            self.actor_inbox.put(Envelope(message, reply_to=future))

        if block:
            return future.get(timeout=timeout)
        else:
            return future

    def stop(self, block=True, timeout=None):
        """
        Send a message to the actor, asking it to stop.

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

        def _stop_result_converter(timeout):
            try:
                ask_future.get(timeout=timeout)
                return True
            except ActorDeadError:
                return False

        converted_future = ask_future.__class__()
        converted_future.set_get_hook(_stop_result_converter)

        if block:
            return converted_future.get(timeout=timeout)
        else:
            return converted_future

    def proxy(self):
        """
        Wraps the :class:`ActorRef` in an :class:`ActorProxy
        <pykka.ActorProxy>`.

        Using this method like this::

            proxy = AnActor.start().proxy()

        is analogous to::

            proxy = ActorProxy(AnActor.start())

        :raise: :exc:`pykka.ActorDeadError` if actor is not available
        :return: :class:`pykka.ActorProxy`
        """
        return ActorProxy(self)
