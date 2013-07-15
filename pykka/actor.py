import logging as _logging
import sys as _sys
import threading as _threading
import uuid as _uuid

try:
    # Python 2.x
    import Queue as _queue
except ImportError:
    # Python 3.x
    import queue as _queue  # noqa

from pykka.exceptions import ActorDeadError as _ActorDeadError
from pykka.future import ThreadingFuture as _ThreadingFuture
from pykka.proxy import ActorProxy as _ActorProxy
from pykka.registry import ActorRegistry as _ActorRegistry

_logger = _logging.getLogger('pykka')


class Actor(object):
    """
    To create an actor:

    1. subclass one of the :class:`Actor` implementations, e.g.
       :class:`GeventActor <pykka.gevent.GeventActor>` or
       :class:`ThreadingActor`,
    2. implement your methods, including :meth:`__init__`, as usual,
    3. call :meth:`Actor.start` on your actor class, passing the method any
       arguments for your constructor.

    To stop an actor, call :meth:`Actor.stop()` or :meth:`ActorRef.stop()`.

    For example::

        import pykka

        class MyActor(pykka.ThreadingActor):
            def __init__(self, my_arg=None):
                super(MyActor, self).__init__()
                ... # My optional init code with access to start() arguments

            def on_start(self):
                ... # My optional setup code in same context as on_receive()

            def on_stop(self):
                ... # My optional cleanup code in same context as on_receive()

            def on_failure(self, exception_type, exception_value, traceback):
                ... # My optional cleanup code in same context as on_receive()

            def on_receive(self, message):
                ... # My optional message handling code for a plain actor

            def a_method(self, ...):
                ... # My regular method to be used through an ActorProxy

        my_actor_ref = MyActor.start(my_arg=...)
        my_actor_ref.stop()
    """

    @classmethod
    def start(cls, *args, **kwargs):
        """
        Start an actor and register it in the
        :class:`ActorRegistry <pykka.ActorRegistry>`.

        Any arguments passed to :meth:`start` will be passed on to the class
        constructor.

        Behind the scenes, the following is happening when you call
        :meth:`start`:

        1. The actor is created:

           1. :attr:`actor_urn` is initialized with the assigned URN.

           2. :attr:`actor_inbox` is initialized with a new actor inbox.

           3. :attr:`actor_ref` is initialized with a :class:`pykka.ActorRef`
              object for safely communicating with the actor.

           4. At this point, your :meth:`__init__()` code can run.

        2. The actor is registered in :class:`pykka.ActorRegistry`.

        3. The actor receive loop is started by the actor's associated
           thread/greenlet.

        :returns: a :class:`ActorRef` which can be used to access the actor in
            a safe manner
        """
        obj = cls(*args, **kwargs)
        assert obj.actor_ref is not None, (
            'Actor.__init__() have not been called. '
            'Did you forget to call super() in your override?')
        _ActorRegistry.register(obj.actor_ref)
        _logger.debug('Starting %s', obj)
        obj._start_actor_loop()
        return obj.actor_ref

    @staticmethod
    def _create_actor_inbox():
        """Internal method for implementors of new actor types."""
        raise NotImplementedError('Use a subclass of Actor')

    @staticmethod
    def _create_future():
        """Internal method for implementors of new actor types."""
        raise NotImplementedError('Use a subclass of Actor')

    def _start_actor_loop(self):
        """Internal method for implementors of new actor types."""
        raise NotImplementedError('Use a subclass of Actor')

    #: The actor URN string is a universally unique identifier for the actor.
    #: It may be used for looking up a specific actor using
    #: :meth:`ActorRegistry.get_by_urn
    #: <pykka.ActorRegistry.get_by_urn>`.
    actor_urn = None

    #: The actor's inbox. Use :meth:`ActorRef.tell`, :meth:`ActorRef.ask`, and
    #: friends to put messages in the inbox.
    actor_inbox = None

    #: The actor's :class:`ActorRef` instance.
    actor_ref = None

    #: A :class:`threading.Event` representing whether or not the actor should
    #: continue processing messages. Use :meth:`stop` to change it.
    actor_stopped = None

    def __init__(self, *args, **kwargs):
        """
        Your are free to override :meth:`__init__`, but you must call your
        superclass' :meth:`__init__` to ensure that fields :attr:`actor_urn`,
        :attr:`actor_inbox`, and :attr:`actor_ref` are initialized.

        You can use :func:`super`::

            super(MyActor, self).__init__()

        Or call you superclass directly::

            pykka.ThreadingActor.__init__(self)
            # or
            pykka.gevent.GeventActor.__init__(self)

        :meth:`__init__` is called before the actor is started and registered
        in :class:`ActorRegistry <pykka.ActorRegistry>`.
        """
        self.actor_urn = _uuid.uuid4().urn
        self.actor_inbox = self._create_actor_inbox()
        self.actor_stopped = _threading.Event()

        self.actor_ref = ActorRef(self)

    def __str__(self):
        return '%(class)s (%(urn)s)' % {
            'class': self.__class__.__name__,
            'urn': self.actor_urn,
        }

    def stop(self):
        """
        Stop the actor.

        It's equivalent to calling :meth:`ActorRef.stop` with ``block=False``.
        """
        self.actor_ref.tell({'command': 'pykka_stop'})

    def _stop(self):
        """
        Stops the actor immediately without processing the rest of the inbox.
        """
        _ActorRegistry.unregister(self.actor_ref)
        self.actor_stopped.set()
        _logger.debug('Stopped %s', self)
        try:
            self.on_stop()
        except Exception:
            self._handle_failure(*_sys.exc_info())

    def _actor_loop(self):
        """
        The actor's event loop.

        This is the method that will be executed by the thread or greenlet.
        """
        try:
            self.on_start()
        except Exception:
            self._handle_failure(*_sys.exc_info())

        while not self.actor_stopped.is_set():
            message = self.actor_inbox.get()
            reply_to = None
            try:
                reply_to = message.pop('pykka_reply_to', None)
                response = self._handle_receive(message)
                if reply_to:
                    reply_to.set(response)
            except Exception:
                if reply_to:
                    _logger.debug(
                        'Exception returned from %s to caller:' % self,
                        exc_info=_sys.exc_info())
                    reply_to.set_exception()
                else:
                    self._handle_failure(*_sys.exc_info())
                    try:
                        self.on_failure(*_sys.exc_info())
                    except Exception:
                        self._handle_failure(*_sys.exc_info())
            except BaseException:
                exception_value = _sys.exc_info()[1]
                _logger.debug(
                    '%s in %s. Stopping all actors.' %
                    (repr(exception_value), self))
                self._stop()
                _ActorRegistry.stop_all()

        while not self.actor_inbox.empty():
            msg = self.actor_inbox.get()
            reply_to = msg.pop('pykka_reply_to', None)
            if reply_to:
                if msg.get('command') == 'pykka_stop':
                    reply_to.set(None)
                else:
                    reply_to.set_exception(_ActorDeadError(
                        '%s stopped before handling the message' %
                        self.actor_ref))

    def on_start(self):
        """
        Hook for doing any setup that should be done *after* the actor is
        started, but *before* it starts processing messages.

        For :class:`ThreadingActor`, this method is executed in the actor's own
        thread, while :meth:`__init__` is executed in the thread that created
        the actor.

        If an exception is raised by this method the stack trace will be
        logged, and the actor will stop.
        """
        pass

    def on_stop(self):
        """
        Hook for doing any cleanup that should be done *after* the actor has
        processed the last message, and *before* the actor stops.

        This hook is *not* called when the actor stops because of an unhandled
        exception. In that case, the :meth:`on_failure` hook is called instead.

        For :class:`ThreadingActor` this method is executed in the actor's own
        thread, immediately before the thread exits.

        If an exception is raised by this method the stack trace will be
        logged, and the actor will stop.
        """
        pass

    def _handle_failure(self, exception_type, exception_value, traceback):
        """Logs unexpected failures, unregisters and stops the actor."""
        _logger.error(
            'Unhandled exception in %s:' % self,
            exc_info=(exception_type, exception_value, traceback))
        _ActorRegistry.unregister(self.actor_ref)
        self.actor_stopped.set()

    def on_failure(self, exception_type, exception_value, traceback):
        """
        Hook for doing any cleanup *after* an unhandled exception is raised,
        and *before* the actor stops.

        For :class:`ThreadingActor` this method is executed in the actor's own
        thread, immediately before the thread exits.

        The method's arguments are the relevant information from
        :func:`sys.exc_info`.

        If an exception is raised by this method the stack trace will be
        logged, and the actor will stop.
        """
        pass

    def _handle_receive(self, message):
        """Handles messages sent to the actor."""
        if message.get('command') == 'pykka_stop':
            return self._stop()
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
        return self.on_receive(message)

    def on_receive(self, message):
        """
        May be implemented for the actor to handle regular non-proxy messages.

        Messages where the value of the "command" key matches "pykka_*" are
        reserved for internal use in Pykka.

        :param message: the message to handle
        :type message: picklable dict

        :returns: anything that should be sent as a reply to the sender
        """
        _logger.warning('Unexpected message received by %s: %s', self, message)

    def _get_attribute_from_path(self, attr_path):
        """
        Traverses the path and returns the attribute at the end of the path.
        """
        attr = self
        for attr_name in attr_path:
            attr = getattr(attr, attr_name)
        return attr


class ThreadingActor(Actor):
    """
    :class:`ThreadingActor` implements :class:`Actor` using regular Python
    threads.

    This implementation is slower than :class:`GeventActor
    <pykka.gevent.GeventActor>`, but can be used in a process with other
    threads that are not Pykka actors.
    """

    use_daemon_thread = False
    """
    A boolean value indicating whether this actor is executed on a thread that
    is a daemon thread (:class:`True`) or not (:class:`False`). This must be
    set before :meth:`pykka.Actor.start` is called, otherwise
    :exc:`RuntimeError` is raised.

    The entire Python program exits when no alive non-daemon threads are left.
    This means that an actor running on a daemon thread may be interrupted at
    any time, and there is no guarantee that cleanup will be done or that
    :meth:`pykka.Actor.on_stop` will be called.

    Actors do not inherit the daemon flag from the actor that made it. It
    always has to be set explicitly for the actor to run on a daemonic thread.
    """

    @staticmethod
    def _create_actor_inbox():
        return _queue.Queue()

    @staticmethod
    def _create_future():
        return _ThreadingFuture()

    def _start_actor_loop(self):
        thread = _threading.Thread(target=self._actor_loop)
        thread.name = thread.name.replace('Thread', self.__class__.__name__)
        thread.daemon = self.use_daemon_thread
        thread.start()


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
        return '<ActorRef for %s>' % str(self)

    def __str__(self):
        return '%(class)s (%(urn)s)' % {
            'urn': self.actor_urn,
            'class': self.actor_class.__name__,
        }

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
        :type message: picklable dict

        :raise: :exc:`pykka.ActorDeadError` if actor is not available
        :return: nothing
        """
        if not self.is_alive():
            raise _ActorDeadError('%s not found' % self)
        self.actor_inbox.put(message)

    def ask(self, message, block=True, timeout=None):
        """
        Send message to actor and wait for the reply.

        The message must be a picklable dict.
        If ``block`` is :class:`False`, it will immediately return a
        :class:`Future <pykka.Future>` instead of blocking.

        If ``block`` is :class:`True`, and ``timeout`` is :class:`None`, as
        default, the method will block until it gets a reply, potentially
        forever. If ``timeout`` is an integer or float, the method will wait
        for a reply for ``timeout`` seconds, and then raise
        :exc:`pykka.Timeout`.

        :param message: message to send
        :type message: picklable dict

        :param block: whether to block while waiting for a reply
        :type block: boolean

        :param timeout: seconds to wait before timeout if blocking
        :type timeout: float or :class:`None`

        :raise: :exc:`pykka.Timeout` if timeout is reached if blocking
        :raise: any exception returned by the receiving actor if blocking
        :return: :class:`pykka.Future`, or response if blocking
        """
        future = self.actor_class._create_future()
        message['pykka_reply_to'] = future
        try:
            self.tell(message)
        except _ActorDeadError:
            future.set_exception()
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
        ask_future = self.ask({'command': 'pykka_stop'}, block=False)

        def _stop_result_converter(timeout):
            try:
                ask_future.get(timeout=timeout)
                return True
            except _ActorDeadError:
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
        return _ActorProxy(self)
