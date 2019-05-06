from __future__ import absolute_import

import logging
import sys
import threading
import uuid

from pykka import ActorDeadError, ActorRef, ActorRegistry, messages


__all__ = ['Actor']

logger = logging.getLogger('pykka')


class Actor(object):
    """
    To create an actor:

    1. subclass one of the :class:`Actor` implementations:

       - :class:`~pykka.ThreadingActor`
       - :class:`~pykka.gevent.GeventActor`
       - :class:`~pykka.eventlet.EventletActor`

    2. implement your methods, including :meth:`__init__`, as usual,
    3. call :meth:`Actor.start` on your actor class, passing the method any
       arguments for your constructor.

    To stop an actor, call :meth:`Actor.stop()` or :meth:`ActorRef.stop()`.

    For example::

        import pykka

        class MyActor(pykka.ThreadingActor):
            def __init__(self, my_arg=None):
                super().__init__()
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
            'Did you forget to call super() in your override?'
        )
        ActorRegistry.register(obj.actor_ref)
        logger.debug('Starting {}'.format(obj))
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
    #: :meth:`ActorRegistry.get_by_urn`.
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

            super().__init__()

        Or call you superclass directly::

            pykka.ThreadingActor.__init__(self)
            # or
            pykka.gevent.GeventActor.__init__(self)

        :meth:`__init__` is called before the actor is started and registered
        in :class:`ActorRegistry <pykka.ActorRegistry>`.
        """
        self.actor_urn = uuid.uuid4().urn
        self.actor_inbox = self._create_actor_inbox()
        self.actor_stopped = threading.Event()

        self.actor_ref = ActorRef(self)

    def __str__(self):
        return '{} ({})'.format(self.__class__.__name__, self.actor_urn)

    def stop(self):
        """
        Stop the actor.

        It's equivalent to calling :meth:`ActorRef.stop` with ``block=False``.
        """
        self.actor_ref.tell(messages._ActorStop())

    def _stop(self):
        """
        Stops the actor immediately without processing the rest of the inbox.
        """
        ActorRegistry.unregister(self.actor_ref)
        self.actor_stopped.set()
        logger.debug('Stopped {}'.format(self))
        try:
            self.on_stop()
        except Exception:
            self._handle_failure(*sys.exc_info())

    def _actor_loop(self):
        """
        The actor's event loop.

        This is the method that will be executed by the thread or greenlet.
        """
        try:
            self.on_start()
        except Exception:
            self._handle_failure(*sys.exc_info())

        while not self.actor_stopped.is_set():
            envelope = self.actor_inbox.get()
            try:
                response = self._handle_receive(envelope.message)
                if envelope.reply_to is not None:
                    envelope.reply_to.set(response)
            except Exception:
                if envelope.reply_to is not None:
                    logger.info(
                        'Exception returned from {} to caller:'.format(self),
                        exc_info=sys.exc_info(),
                    )
                    envelope.reply_to.set_exception()
                else:
                    self._handle_failure(*sys.exc_info())
                    try:
                        self.on_failure(*sys.exc_info())
                    except Exception:
                        self._handle_failure(*sys.exc_info())
            except BaseException:
                exception_value = sys.exc_info()[1]
                logger.debug(
                    '{!r} in {}. Stopping all actors.'.format(
                        exception_value, self
                    )
                )
                self._stop()
                ActorRegistry.stop_all()

        while not self.actor_inbox.empty():
            envelope = self.actor_inbox.get()
            if envelope.reply_to is not None:
                if isinstance(envelope.message, messages._ActorStop):
                    envelope.reply_to.set(None)
                else:
                    envelope.reply_to.set_exception(
                        exc_info=(
                            ActorDeadError,
                            ActorDeadError(
                                '{} stopped before handling the message'.format(
                                    self.actor_ref
                                )
                            ),
                            None,
                        )
                    )

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
        logger.error(
            'Unhandled exception in {}:'.format(self),
            exc_info=(exception_type, exception_value, traceback),
        )
        ActorRegistry.unregister(self.actor_ref)
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
        message = messages._upgrade_internal_message(message)
        if isinstance(message, messages._ActorStop):
            return self._stop()
        if isinstance(message, messages.ProxyCall):
            callee = self._get_attribute_from_path(message.attr_path)
            return callee(*message.args, **message.kwargs)
        if isinstance(message, messages.ProxyGetAttr):
            attr = self._get_attribute_from_path(message.attr_path)
            return attr
        if isinstance(message, messages.ProxySetAttr):
            parent_attr = self._get_attribute_from_path(message.attr_path[:-1])
            attr_name = message.attr_path[-1]
            return setattr(parent_attr, attr_name, message.value)
        return self.on_receive(message)

    def on_receive(self, message):
        """
        May be implemented for the actor to handle regular non-proxy messages.

        :param message: the message to handle
        :type message: any

        :returns: anything that should be sent as a reply to the sender
        """
        logger.warning(
            'Unexpected message received by {}: {}'.format(self, message)
        )

    def _get_attribute_from_path(self, attr_path):
        """
        Traverses the path and returns the attribute at the end of the path.
        """
        attr = self
        for attr_name in attr_path:
            attr = getattr(attr, attr_name)
        return attr

    def _introspect_attribute_from_path(self, attr_path):
        """Get attribute information from ``__dict__`` on the container."""
        if not attr_path:
            return self

        parent = self._get_attribute_from_path(attr_path[:-1])
        parent_attrs = self._introspect_attributes(parent)
        attr_name = attr_path[-1]

        try:
            return parent_attrs[attr_name]
        except KeyError:
            raise AttributeError(
                'type object {!r} has no attribute {!r}'.format(
                    parent.__class__.__name__, attr_name
                )
            )

    def _introspect_attributes(self, obj):
        """Combine ``__dict__`` from ``obj`` and all its superclasses."""
        result = {}
        for cls in reversed(obj.__class__.mro()):
            result.update(cls.__dict__)
        if hasattr(obj, '__dict__'):
            result.update(obj.__dict__)
        return result
