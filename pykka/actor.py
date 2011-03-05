import collections
import logging
import multiprocessing
import multiprocessing.dummy
import uuid

from pykka.future import ThreadingFuture
from pykka.proxy import ActorProxy
from pykka.registry import ActorRegistry

logger = logging.getLogger('pykka')


class Actor(object):
    """
    To create an actor:

    1. subclass one of the :class:`Actor` implementations, e.g.
       :class:`pykka.gevent.GeventActor` or :class:`ThreadingActor`,
    2. implement your methods, including :meth:`__init__`, as usual,
    3. call :meth:`Actor.start` on your actor class, passing the method any
       arguments for your constructor.

    To stop an actor, call :meth:`Actor.stop()` or :meth:`ActorRef.stop()`.

    For example::

        from pykka.actor import ThreadingActor

        class MyActor(ThreadingActor):
            def __init__(self, my_arg=None):
                ... # my init code

            def react(self, message):
                ... # my react code for a plain actor

            def a_method(self, ...):
                ... # my regular method to be used through an ActorProxy

        my_actor_ref = MyActor.start(my_arg=...)
        my_actor_ref.stop()
    """

    @classmethod
    def start(cls, *args, **kwargs):
        """
        Start an actor and register it in the
        :class:`pykka.registry.ActorRegistry`.

        Any arguments passed to :meth:`start` will be passed on to the class
        constructor.

        Returns a :class:`ActorRef` which can be used to access the actor in a
        safe manner.

        Behind the scenes, the following is happening when you call
        :meth:`start`::

            Actor.start()
                Actor.__new__()
                    superclass.__new__()
                    superclass.__init__()
                    UUID assignment
                    Inbox creation
                    ActorRef creation
                Actor.__init__()        # Your code can run here
                superclass.start()
                ActorRegistry.register()
        """
        obj = cls(*args, **kwargs)
        cls._superclass.start(obj)
        logger.debug('Started %s', obj)
        ActorRegistry.register(obj.actor_ref)
        return obj.actor_ref

    @classmethod
    def start_proxy(cls, *args, **kwargs):
        """
        Just like :meth:`start`, but wraps the returned :class:`ActorRef` in an
        :class:`ActorProxy`.
        """
        return ActorProxy(cls.start(*args, **kwargs))

    #: The actor URN string is a universally unique identifier for the actor.
    #: It may be used for looking up a specific actor using
    #: :meth:`pykka.registry.ActorRegistry.get_by_urn`.
    actor_urn = None

    #: The actors inbox. Use :meth:`ActorRef.send_one_way` and friends to put
    #: messages in the inbox.
    actor_inbox = None

    #: The actor's :class:`ActorRef` instance.
    actor_ref = None

    #: Wether or not the actor should continue processing messages. Use
    #: :meth:`stop` to change it.
    actor_runnable = True

    def __new__(cls, *args, **kwargs):
        obj = cls._superclass.__new__(cls)
        cls._superclass.__init__(obj)
        obj.actor_urn = uuid.uuid4().urn
        # pylint: disable = W0212
        obj.actor_inbox = obj._new_actor_inbox()
        # pylint: enable = W0212
        obj.actor_ref = ActorRef(obj)
        return obj

    # pylint: disable = W0231
    def __init__(self):
        """
        Your are free to override :meth:`__init__` and do any setup you need to
        do. You should not call ``super(YourClass, self).__init__(...)``, as
        that has already been done when your constructor is called.

        When :meth:`__init__` is called, the internal fields
        :attr:`actor_urn`, :attr:`actor_inbox`, and :attr:`actor_ref` are
        already set, but the actor is not started or registered in
        :class:`pykka.registry.ActorRegistry`.
        """
        pass
    # pylint: enable = W0231

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
        logger.debug('Stopped %s', self)

    # pylint: disable = W0703
    def _run(self):
        """
        The actor's main method.

        :class:`pykka.gevent.GeventActor` expects this method to be named
        :meth:`_run`.

        :class:`ThreadingActor` expects this method to be named :meth:`run`.
        """
        self.actor_runnable = True
        while self.actor_runnable:
            message = self.actor_inbox.get()
            try:
                response = self._react(message)
                if 'reply_to' in message:
                    message['reply_to'].set(response)
            except Exception as exception:
                if 'reply_to' in message:
                    message['reply_to'].set_exception(exception)
    # pylint: enable = W0703

    def _react(self, message):
        """Reacts to messages sent to the actor."""
        if message.get('command') == 'pykka_get_attributes':
            return self._get_attributes()
        if message.get('command') == 'pykka_stop':
            return self.stop()
        if message.get('command') == 'pykka_call':
            callee = self._get_attribute_from_path(message['attr_path'])
            return callee(*message['args'], **message['kwargs'])
        if message.get('command') == 'pykka_getattr':
            attr = self._get_attribute_from_path(message['attr_path'])
            return attr
        if message.get('command') == 'pykka_setattr':
            parent_attr = self._get_attribute_from_path(
                message['attr_path'][:-1])
            attr_name = message['attr_path'][-1]
            return setattr(parent_attr, attr_name, message['value'])
        return self.react(message)

    def react(self, message):
        """
        May be implemented for the actor to handle non-proxy messages.

        Messages where the value of the 'command' key matches 'pykka_*' are
        reserved for internal use in Pykka.

        :param message: the message to handle
        :type message: picklable dict

        :returns: anything that should be sent as a reply to the sender
        """
        raise NotImplementedError

    def _is_exposable_attribute(self, attr_name):
        """
        Returns true for any attribute name that may be exposed through
        :class:`ActorProxy`.
        """
        return not attr_name.startswith('_')

    def _is_traversable_attribute(self, attr):
        """
        Returns true for any attribute that may be traversed from another
        actor through :class:`ActorProxy`.
        """
        return hasattr(attr, 'pykka_traversable')

    def _get_attribute_from_path(self, attr_path):
        """
        Traverses the path and returns the attribute at the end of the path.
        """
        attr = self
        for attr_name in attr_path:
            attr = getattr(attr, attr_name)
        return attr

    def _get_attributes(self):
        """Gathers attribute information needed by :class:`ActorProxy`."""
        result = {}
        attr_paths_to_visit = [[attr_name] for attr_name in dir(self)]
        while attr_paths_to_visit:
            attr_path = attr_paths_to_visit.pop(0)
            if self._is_exposable_attribute(attr_path[-1]):
                attr = self._get_attribute_from_path(attr_path)
                result[tuple(attr_path)] = {
                    'callable': isinstance(attr, collections.Callable),
                    'traversable': self._is_traversable_attribute(attr),
                }
                if self._is_traversable_attribute(attr):
                    for attr_name in dir(attr):
                        attr_paths_to_visit.append(attr_path + [attr_name])
        return result


# pylint: disable = R0901
class ThreadingActor(Actor, multiprocessing.dummy.Process):
    """
    :class:`ThreadingActor` implements :class:`Actor` using regular Python
    threads, via the :mod:`multiprocessing.dummy` package.

    This implementation is slower than :class:`pykka.gevent.GeventActor`, but
    can be used in a process with other threads that are not Pykka actors.
    """

    _superclass = multiprocessing.dummy.Process
    _future_class = ThreadingFuture

    def _new_actor_inbox(self):
        return multiprocessing.Queue()

    def run(self):
        return Actor._run(self)

    def react(self, message):
        raise NotImplementedError
# pylint: enable = R0901


class ActorRef(object):
    """
    Reference to a running actor which may safely be passed around.

    :class:`ActorRef` instances are returned by :meth:`Actor.start` and the
    lookup methods in :class:`pykka.registry.ActorRegistry`. You should never
    need to create :class:`ActorRef` instances yourself.

    :param actor: the actor to wrap
    :type actor: :class:`Actor`
    """

    #: See :attr:`Actor.actor_urn`
    actor_urn = None

    def __init__(self, actor):
        self.actor_urn = actor.actor_urn
        self.actor_class = actor.__class__
        self.actor_inbox = actor.actor_inbox
        # pylint: disable = W0212
        self._future_class = actor._future_class
        # pylint: enable = W0212

    def __repr__(self):
        return '<ActorRef for %s>' % str(self)

    def __str__(self):
        return '%(class)s (%(urn)s)' % {
            'urn': self.actor_urn,
            'class': self.actor_class.__name__,
        }

    def send_one_way(self, message):
        """
        Send message to actor without waiting for any response.

        Will generally not block, but if the underlying queue is full it will
        block until a free slot is available.

        :param message: message to send
        :type message: picklable dict

        :return: nothing
        """
        self.actor_inbox.put(message)

    def send_request_reply(self, message, block=True, timeout=None):
        """
        Send message to actor and wait for the reply.

        The message must be a picklable dict.
        If ``block`` is :class:`False`, it will immediately return a
        :class:`pykka.future.Future` instead of blocking.

        If ``block`` is :class:`True`, and ``timeout`` is :class:`None`, as
        default, the method will block until it gets a reply, potentially
        forever. If ``timeout`` is an integer or float, the method will wait
        for a reply for ``timeout`` seconds, and then raise
        :exc:`pykka.future.Timeout`.

        :param message: message to send
        :type message: picklable dict

        :param block: whether to block while waiting for a reply
        :type block: boolean

        :param timeout: seconds to wait before timeout if blocking
        :type timeout: float or :class:`None`

        :return: :class:`pykka.future.Future` or response
        """
        future = self._future_class()
        message['reply_to'] = future
        self.send_one_way(message)
        if block:
            return future.get(timeout=timeout)
        else:
            return future

    def stop(self, block=True, timeout=None):
        """
        Send a message to the actor, asking it to stop.

        ``block`` and ``timeout`` works as for :meth:`send_request_reply`.
        """
        self.send_request_reply({'command': 'pykka_stop'}, block, timeout)
