import gevent
import gevent.queue
import logging
import uuid

from pykka.proxy import ActorProxy
from pykka.ref import ActorRef
from pykka.registry import ActorRegistry

logger = logging.getLogger('pykka')


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

    actor_urn = None
    actor_inbox = None
    actor_ref = None
    actor_runnable = True

    @classmethod
    def start(cls, *args, **kwargs):
        """
        Start an actor and register it in the :class:`ActorRegistry`.

        Any arguments passed to :meth:`start` will be passed on to the class
        constructor.

        Returns a :class:`ActorRef` which can be used to access the actor in a
        safe manner.

        Behind the scenes, the following is happening when you call
        :meth:`start`::

            Actor.start()
                Actor.__new__()
                    Greenlet.__new__()
                    Greenlet.__init__()
                    UUID assignment
                    Inbox creation
                    ActorRef creation
                Actor.__init__()        # Your code can run here
                Greenlet.start()
                ActorRegistry.register()
        """
        obj = cls(*args, **kwargs)
        gevent.Greenlet.start(obj)
        logger.debug(u'Started %s', obj)
        ActorRegistry.register(obj.actor_ref)
        return obj.actor_ref

    @classmethod
    def start_proxy(cls, *args, **kwargs):
        """
        Just like :meth:`start`, but wraps the returned :class:`ActorRef` in an
        :class:`ActorProxy`.
        """
        return ActorProxy(cls.start(*args, **kwargs))

    def __new__(cls, *args, **kwargs):
        obj = gevent.Greenlet.__new__(cls, *args, **kwargs)
        gevent.Greenlet.__init__(obj)
        obj.actor_urn = uuid.uuid4().urn
        obj.actor_inbox = gevent.queue.Queue()
        obj.actor_ref = ActorRef(obj)
        return obj

    # pylint: disable=W0231
    def __init__(self):
        """
        Your are free to override :meth:`__init__` and do any setup you need to
        do. You should not call ``super(YourClass, self).__init__(...)``, as
        that has already been done when your constructor is called.

        When :meth:`__init__` is called, the internal fields
        :attr:`actor_urn`, :attr:`actor_inbox`, and :attr:`actor_ref` are
        already set, but the actor is not started or registered in
        :class:`ActorRegistry`.
        """
        pass
    # pylint: enable=W0231

    def __str__(self):
        return '%(class)s (%(urn)s)' % {
            'class': self.__class__.__name__,
            'urn': self.actor_urn,
        }

    def stop(self):
        """
        Stop the actor.

        The actor will finish processing any messages already in its queue
        before stopping. It may not be restarted.
        """
        self.actor_runnable = False
        ActorRegistry.unregister(self.actor_ref)
        logger.debug(u'Stopped %s', self)

    def _run(self):
        """The Greenlet main method"""
        self.actor_runnable = True
        while self.actor_runnable:
            message = self.actor_inbox.get()
            response = self._react(message)
            if 'reply_to' in message:
                message['reply_to'].set(response)

    def _react(self, message):
        """Reacts to messages sent to the actor."""
        if message.get('command') == 'get_attributes':
            return self._get_attributes()
        if message.get('command') == 'stop':
            return self.stop()
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

    def _is_exposable_attribute(self, attr):
        """
        Returns true for any attribute name that may be exposed through
        :class:`ActorProxy`.
        """
        return not attr.startswith('_')

    def _get_attributes(self):
        """Gathers attribute information needed by :class:`ActorProxy`."""
        result = {}
        for attr in dir(self):
            if self._is_exposable_attribute(attr):
                result[attr] = {
                    'callable': callable(getattr(self, attr)),
                }
        return result
