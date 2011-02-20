class ActorProxy(object):
    """
    An :class:`ActorProxy` wraps an :class:`pykka.actor.ActorRef`. The proxy
    allows the referenced actor to be used through a normal method calls and
    field access.

    You can create an :class:`ActorProxy` from any
    :class:`pykka.actor.ActorRef`::

        actor_ref = MyActor.start()
        actor_proxy = ActorProxy(actor_ref)

    You can also get an :class:`ActorProxy` directly when starting the actor::

        actor_proxy = MyActor.start_proxy()

    An example of :class:`ActorProxy` usage:

    .. literalinclude:: ../examples/counter.py

    :param actor_ref: reference to the actor to proxy
    :type actor_ref: :class:`pykka.actor.ActorRef`
    """

    def __init__(self, actor_ref):
        self._actor_ref = actor_ref
        self._actor_attributes = self._get_attributes()

    def __repr__(self):
        return '<ActorProxy for %s>' % self._actor_ref

    def _get_attributes(self):
        return self._actor_ref.send_request_reply(
            {'command': 'pykka_get_attributes'})

    def __getattr__(self, name):
        """Get a field or callable from the actor."""
        if name not in self._actor_attributes:
            self._actor_attributes = self._get_attributes()
        attr_info = self._actor_attributes.get(name)
        if attr_info is None:
            raise AttributeError('%s has no attribute "%s"' % (self, name))
        if attr_info['callable']:
            return _CallableProxy(self._actor_ref, name)
        else:
            return self._get_actor_field(name)

    def __setattr__(self, name, value):
        """Set a field on the actor."""
        if name.startswith('_'):
            return super(ActorProxy, self).__setattr__(name, value)
        return self._set_actor_field(name, value)

    def __dir__(self):
        result = ['__class__']
        result += self.__class__.__dict__.keys()
        result += self.__dict__.keys()
        result += self._actor_attributes.keys()
        return sorted(result)

    def _get_actor_field(self, name):
        """Get a field from the actor."""
        message = {
            'command': 'pykka_getattr',
            'attribute': name,
        }
        return self._actor_ref.send_request_reply(message, block=False)

    def _set_actor_field(self, name, value):
        """Set a field on the actor."""
        message = {
            'command': 'pykka_setattr',
            'attribute': name,
            'value': value,
        }
        return self._actor_ref.send_request_reply(message, block=False)


class _CallableProxy(object):
    """Internal helper class for proxying callables."""
    def __init__(self, ref, attribute):
        self._actor_ref = ref
        self._attribute = attribute

    def __call__(self, *args, **kwargs):
        message = {
            'command': 'pykka_call',
            'attribute': self._attribute,
            'args': args,
            'kwargs': kwargs,
        }
        return self._actor_ref.send_request_reply(message, block=False)
