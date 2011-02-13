class ActorProxy(object):
    """
    An :class:`ActorProxy` wraps an :class:`ActorRef`. The proxy allows the
    referenced actor to be used through a normal method calls and field
    access.

    You can create an :class:`ActorProxy` from any :class:`ActorRef` by::

        actor_proxy = ActorProxy(actor_ref)
    """

    def __init__(self, actor_ref):
        self._actor_ref = actor_ref
        self._actor_attributes = self._get_attributes()

    def __repr__(self):
        return '<ActorProxy for %s>' % self._actor_ref

    def _get_attributes(self):
        return self._actor_ref.send_request_reply(
            {'command': 'get_attributes'})

    def __getattr__(self, name):
        if name not in self._actor_attributes:
            self._actor_attributes = self._get_attributes()
        attr_info = self._actor_attributes.get(name)
        if attr_info is None:
            raise AttributeError('%s has no attribute "%s"' % (self, name))
        if attr_info['callable']:
            return CallableProxy(self._actor_ref, name)
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
            'command': 'read',
            'attribute': name,
        }
        return self._actor_ref.send_request_reply(message, block=False)

    def _set_actor_field(self, name, value):
        """Set a field on the actor."""
        message = {
            'command': 'write',
            'attribute': name,
            'value': value,
        }
        return self._actor_ref.send_request_reply(message, block=False)


class CallableProxy(object):
    """Helper class for proxying callables."""
    def __init__(self, ref, attribute):
        self._actor_ref = ref
        self._attribute = attribute

    def __call__(self, *args, **kwargs):
        message = {
            'command': 'call',
            'attribute': self._attribute,
            'args': args,
            'kwargs': kwargs,
        }
        return self._actor_ref.send_request_reply(message, block=False)
