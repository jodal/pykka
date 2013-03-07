import collections as _collections
import sys as _sys

from pykka.exceptions import ActorDeadError as _ActorDeadError


class ActorProxy(object):
    """
    An :class:`ActorProxy` wraps an :class:`ActorRef <pykka.ActorRef>`
    instance. The proxy allows the referenced actor to be used through regular
    method calls and field access.

    You can create an :class:`ActorProxy` from any :class:`ActorRef
    <pykka.ActorRef>`::

        actor_ref = MyActor.start()
        actor_proxy = ActorProxy(actor_ref)

    You can also get an :class:`ActorProxy` by using :meth:`proxy()
    <pykka.ActorRef.proxy>`::

        actor_proxy = MyActor.start().proxy()

    When reading an attribute or getting a return value from a method, you get
    a :class:`Future <pykka.Future>` object back. To get the enclosed value
    from the future, you must call :meth:`get() <pykka.Future.get>` on the
    returned future::

        print actor_proxy.string_attribute.get()
        print actor_proxy.count().get() + 1

    If you call a method just for it's side effects and do not care about the
    return value, you do not need to accept the returned future or call
    :meth:`get() <pykka.Future.get>` on the future. Simply call the method, and
    it will be executed concurrently with your own code::

        actor_proxy.method_with_side_effect()

    If you want to block your own code from continuing while the other method
    is processing, you can use :meth:`get() <pykka.Future.get>` to block until
    it completes::

        actor_proxy.method_with_side_effect().get()

    An actor can use a proxy to itself to schedule work for itself. The
    scheduled work will only be done after the current message and all messages
    already in the inbox are processed.

    For example, if an actor can split a time consuming task into multiple
    parts, and after completing each part can ask itself to start on the next
    part using proxied calls or messages to itself, it can react faster to
    other incoming messages as they will be interleaved with the parts of the
    time consuming task. This is especially useful for being able to stop the
    actor in the middle of a time consuming task.

    To create a proxy to yourself, use the actor's :attr:`actor_ref
    <pykka.Actor.actor_ref>` attribute::

        proxy_to_myself_in_the_future = self.actor_ref.proxy()

    If you create a proxy in your actor's constructor or :meth:`on_start
    <pykka.Actor.on_start>` method, you can create a nice API for deferring
    work to yourself in the future::

        def __init__(self):
            ...
            self.in_future = self.actor_ref.proxy()
            ...

        def do_work(self):
            ...
            self.in_future.do_more_work()
            ...

        def do_more_work(self):
            ...

    An example of :class:`ActorProxy` usage:

    .. literalinclude:: ../examples/counter.py

    :param actor_ref: reference to the actor to proxy
    :type actor_ref: :class:`pykka.ActorRef`

    :raise: :exc:`pykka.ActorDeadError` if actor is not available
    """

    #: The actor's :class:`pykka.ActorRef` instance.
    actor_ref = None

    def __init__(self, actor_ref, attr_path=None):
        if not actor_ref.is_alive():
            raise _ActorDeadError('%s not found' % actor_ref)
        self.actor_ref = actor_ref
        self._actor = actor_ref._actor
        self._attr_path = attr_path or tuple()
        self._known_attrs = self._get_attributes()
        self._actor_proxies = {}
        self._callable_proxies = {}

    def _get_attributes(self):
        """Gathers actor attributes needed to proxy the actor"""
        result = {}
        attr_paths_to_visit = [[attr_name] for attr_name in dir(self._actor)]
        while attr_paths_to_visit:
            attr_path = attr_paths_to_visit.pop(0)
            if self._is_exposable_attribute(attr_path[-1]):
                attr = self._actor._get_attribute_from_path(attr_path)
                result[tuple(attr_path)] = {
                    'callable': self._is_callable_attribute(attr),
                    'traversable': self._is_traversable_attribute(attr),
                }
                if self._is_traversable_attribute(attr):
                    for attr_name in dir(attr):
                        attr_paths_to_visit.append(attr_path + [attr_name])
        return result

    def _is_exposable_attribute(self, attr_name):
        """
        Returns true for any attribute name that may be exposed through
        :class:`ActorProxy`.
        """
        return not attr_name.startswith('_')

    def _is_callable_attribute(self, attr):
        """Returns true for any attribute that is callable."""
        # isinstance(attr, collections.Callable), as recommended by 2to3, does
        # not work on CPython 2.6.4 if the attribute is an Queue.Queue, but
        # works on 2.6.6.
        if _sys.version_info < (3,):
            return callable(attr)
        else:
            return isinstance(attr, _collections.Callable)

    def _is_traversable_attribute(self, attr):
        """
        Returns true for any attribute that may be traversed from another
        actor through a proxy.
        """
        return hasattr(attr, 'pykka_traversable')

    def __repr__(self):
        return '<ActorProxy for %s, attr_path=%s>' % (
            self.actor_ref, self._attr_path)

    def __dir__(self):
        result = ['__class__']
        result += list(self.__class__.__dict__.keys())
        result += list(self.__dict__.keys())
        result += [
            attr_path[0] for attr_path in list(self._known_attrs.keys())]
        return sorted(result)

    def __getattr__(self, name):
        """Get a field or callable from the actor."""
        attr_path = self._attr_path + (name,)
        if attr_path not in self._known_attrs:
            self._known_attrs = self._get_attributes()
        attr_info = self._known_attrs.get(attr_path)
        if attr_info is None:
            raise AttributeError('%s has no attribute "%s"' % (self, name))
        if attr_info['callable']:
            if attr_path not in self._callable_proxies:
                self._callable_proxies[attr_path] = _CallableProxy(
                    self.actor_ref, attr_path)
            return self._callable_proxies[attr_path]
        elif attr_info['traversable']:
            if attr_path not in self._actor_proxies:
                self._actor_proxies[attr_path] = ActorProxy(
                    self.actor_ref, attr_path)
            return self._actor_proxies[attr_path]
        else:
            message = {
                'command': 'pykka_getattr',
                'attr_path': attr_path,
            }
            return self.actor_ref.ask(message, block=False)

    def __setattr__(self, name, value):
        """
        Set a field on the actor.

        Blocks until the field is set to check if any exceptions was raised.
        """
        if name == 'actor_ref' or name.startswith('_'):
            return super(ActorProxy, self).__setattr__(name, value)
        attr_path = self._attr_path + (name,)
        message = {
            'command': 'pykka_setattr',
            'attr_path': attr_path,
            'value': value,
        }
        return self.actor_ref.ask(message)


class _CallableProxy(object):
    """Internal helper class for proxying callables."""
    def __init__(self, ref, attr_path):
        self.actor_ref = ref
        self._attr_path = attr_path

    def __call__(self, *args, **kwargs):
        message = {
            'command': 'pykka_call',
            'attr_path': self._attr_path,
            'args': args,
            'kwargs': kwargs,
        }
        return self.actor_ref.ask(message, block=False)
