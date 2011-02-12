import gevent
import gevent.queue
import sys
import uuid

from pykka.proxy import ActorProxy
from pykka.registry import ActorRegistry


class Actor(gevent.Greenlet):
    """
    An actor has the following characteristics:

    - It does not share state with anybody else.

    - It can have its own state.

    - It can only communicate with other actors by sending and receiving
      messages.

    - It can only send messages to actors whose address it has.

    - When an actor receives a message it may take actions like:

      - altering its own state, e.g. so that it can react differently to a
        future message,
      - sending messages to other actors, or
      - starting new actors.

    - None of the actions are required, and they may be applied in any order.

    - It only processes one message at a time. In other words, a single actor
      does not give you any concurrency, and it does not need to use e.g. locks
      to protect its own state.

    To create an actor:

    1. subclass :class:`Actor`,
    2. implement your methods, including :meth:`__init__`, as usual,
    3. call :meth:`Actor.start(...)` on the actor class, passing the method any
       arguments for your constructor.

    To stop an actor, call :meth:`Actor.stop()`.
    """

    @classmethod
    def start(cls, *args, **kwargs):
        """
        Start an actor and register it in the :class:`ActorRegistry`.

        Any arguments passed to :meth:`start` will be passed on to the class
        constructor.

        Returns a :class:`ActorProxy` which can be used to access the actor in
        a safe manner.

        Behind the scenes, the following is happening when you call
        :meth:`start`::

            Actor.start()
                Actor.__new__()
                    Greenlet.__new__()
                    Greenlet.__init__()
                    UUID assignment
                    Inbox creation
                    Proxy creation
                Actor.__init__()        # Your code can run here
                Greenlet.start()
                ActorRegistry.register()
        """
        obj = cls(*args, **kwargs)
        super(Actor, obj).start()
        ActorRegistry.register(obj._actor_proxy)
        return obj._actor_proxy

    def __new__(cls, *args, **kwargs):
        obj = super(Actor, cls).__new__(cls, *args, **kwargs)
        super(Actor, obj).__init__()
        obj._actor_urn = uuid.uuid4().urn
        obj._actor_inbox = gevent.queue.Queue()
        obj._actor_proxy = ActorProxy(obj)
        return obj

    def __init__(self):
        """
        Your are free to override :meth:`__init__` and do any setup you need to
        do. You should not call ``super(YourClass, self).__init__(...)``, as
        that has already been done when your constructor is called.

        When :meth:`__init__` is called, the internal fields
        :attr:`_actor_urn`, :attr:`_actor_inbox`, and :attr:`_actor_proxy` are
        already set, but the actor is not started or registered in
        :class:`ActorRegistry`.
        """
        pass

    def __str__(self):
        return '%(class)s (%(urn)s)' % {
            'class': self.__class__.__name__,
            'urn': self._actor_urn,
        }

    def stop(self):
        """
        Stop the actor and terminate its thread.

        The actor will not stop until it is done processing the current
        message.
        """
        self.runnable = False
        ActorRegistry.unregister(self._actor_proxy)

    def _run(self):
        self.runnable = True
        try:
            while self.runnable:
                self._event_loop()
        except KeyboardInterrupt:
            sys.exit()

    def _event_loop(self):
        """The actor's event loop which is called continously to handle
        incoming messages, one at the time."""
        message = self._actor_inbox.get()
        response = self._react(message)
        if 'reply_to' in message:
            message['reply_to'].set(response)

    def _react(self, message):
        """Reacts to messages sent to the actor."""
        if message.get('command') == 'call':
            return getattr(self, message['attribute'])(
                *message['args'], **message['kwargs'])
        if message.get('command') == 'read':
            return getattr(self, message['attribute'])
        if message.get('command') == 'write':
            return setattr(self, message['attribute'], message['value'])
        return self.react(message)

    def react(self, message):
        """May be implemented for the actor to handle custom messages."""
        raise NotImplementedError

    def get_attributes(self):
        """Returns a dict where the keys are all the available attributes and
        the value is whether the attribute is callable."""
        result = {}
        for attr in dir(self):
            if not attr.startswith('_'):
                result[attr] = callable(getattr(self, attr))
        return result
