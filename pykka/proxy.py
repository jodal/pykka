from pykka import ActorDeadError as _ActorDeadError


class ActorProxy(object):
    """
    An :class:`ActorProxy` wraps an :class:`ActorRef <pykka.actor.ActorRef>`
    instance. The proxy allows the referenced actor to be used through
    regular method calls and field access.

    You can create an :class:`ActorProxy` from any
    :class:`ActorRef <pykka.actor.ActorRef>`::

        actor_ref = MyActor.start()
        actor_proxy = ActorProxy(actor_ref)

    You can also get an :class:`ActorProxy` by using
    :meth:`proxy() <pykka.actor.ActorRef.proxy>`::

        actor_proxy = MyActor.start().proxy()

    When reading an attribute or getting a return value from a method, you get
    a :class:`Future <pykka.future.Future>` object back. To get the enclosed
    value from the future, you must call :meth:`get()
    <pykka.future.Future.get>` on the returned future::

        print actor_proxy.string_attribute.get()
        print actor_proxy.count().get() + 1

    If you call a method just for it's side effects and do not care about the
    return value, you do not need to accept the returned future or call
    :meth:`get() <pykka.future.Future.get>` on the future. Simply call the
    method, and it will be executed concurrently with your own code::

        actor_proxy.method_with_side_effect()

    If you want to block your own code from continuing while the other method
    is processing, you can use :meth:`get() <pykka.future.Future.get>` to block
    until it completes::

        actor_proxy.method_with_side_effect().get()

    An example of :class:`ActorProxy` usage:

    .. literalinclude:: ../examples/counter.py

    :param actor_ref: reference to the actor to proxy
    :type actor_ref: :class:`pykka.actor.ActorRef`

    :raise: :exc:`pykka.ActorDeadError` if actor is not available
    """

    #: The actor's :class:`pykka.actor.ActorRef` instance.
    actor_ref = None

    def __init__(self, actor_ref, attr_path=None):
        if not actor_ref.is_alive():
            raise _ActorDeadError('%s not found' % actor_ref)
        self.actor_ref = actor_ref
        self._attr_path = attr_path or tuple()
        self._known_attrs = None
        self._actor_proxies = {}
        self._callable_proxies = {}

    def _update_attrs(self):
        self._known_attrs = self.actor_ref.ask(
            {'command': 'pykka_get_attributes'})

    def __repr__(self):
        return '<ActorProxy for %s, attr_path=%s>' % (self.actor_ref,
            self._attr_path)

    def __dir__(self):
        if self._known_attrs is None:
            self._update_attrs()
        result = ['__class__']
        result += list(self.__class__.__dict__.keys())
        result += list(self.__dict__.keys())
        result += [attr_path[0]
            for attr_path in list(self._known_attrs.keys())]
        return sorted(result)

    def __getattr__(self, name):
        """Get a field or callable from the actor."""
        attr_path = self._attr_path + (name,)
        if self._known_attrs is None or attr_path not in self._known_attrs:
            self._update_attrs()
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
