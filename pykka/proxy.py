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

    def __init__(self, actor_ref, attr_path=None):
        self._actor_ref = actor_ref
        self._attr_path = attr_path or tuple()
        self._actor_attributes = self._get_attributes()

    def _get_attributes(self):
        return self._actor_ref.send_request_reply(
            {'command': 'pykka_get_attributes'})

    def __repr__(self):
        return '<ActorProxy for %s, attr_path=%s>' % (self._actor_ref,
            self._attr_path)

    def __dir__(self):
        result = ['__class__']
        result += self.__class__.__dict__.keys()
        result += self.__dict__.keys()
        result += [attr_path[0] for attr_path in self._actor_attributes.keys()]
        return sorted(result)

    def __getattr__(self, name):
        """Get a field or callable from the actor."""
        attr_path = self._attr_path + (name,)
        if attr_path not in self._actor_attributes:
            self._actor_attributes = self._get_attributes()
        attr_info = self._actor_attributes.get(attr_path)
        if attr_info is None:
            raise AttributeError('%s has no attribute "%s"' % (self, name))
        if attr_info['callable']:
            return _CallableProxy(self._actor_ref, attr_path)
        elif attr_info['traversable']:
            return ActorProxy(self._actor_ref, attr_path)
        else:
            message = {
                'command': 'pykka_getattr',
                'attr_path': attr_path,
            }
            return self._actor_ref.send_request_reply(message, block=False)

    def __setattr__(self, name, value):
        """
        Set a field on the actor.

        Blocks until the field is set to check if any exceptions was raised.
        """
        if name.startswith('_'):
            return super(ActorProxy, self).__setattr__(name, value)
        attr_path = self._attr_path + (name,)
        message = {
            'command': 'pykka_setattr',
            'attr_path': attr_path,
            'value': value,
        }
        return self._actor_ref.send_request_reply(message)


class _CallableProxy(object):
    """Internal helper class for proxying callables."""
    def __init__(self, ref, attr_path):
        self._actor_ref = ref
        self._attr_path = attr_path

    def __call__(self, *args, **kwargs):
        message = {
            'command': 'pykka_call',
            'attr_path': self._attr_path,
            'args': args,
            'kwargs': kwargs,
        }
        return self._actor_ref.send_request_reply(message, block=False)
