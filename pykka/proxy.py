import gevent.event

from pykka.future import Future


class ActorProxy(object):
    """
    Proxy for a running actor which allows the actor to be used through a
    normal method calls and field accesses.

    You should never need to create :class:`ActorProxy` instances yourself.
    """

    def __init__(self, actor):
        self._actor_class = actor.__class__
        self._actor_inbox = actor.inbox
        self._actor_attributes = actor.get_attributes()

    def send(self, message):
        """
        Send message to actor.

        The message must be a picklable dict.
        """
        self._actor_inbox.put(message)

    def __getattr__(self, name):
        if not name in self._actor_attributes:
            self._actor_attributes = self.get_attributes().get()
            if not name in self._actor_attributes:
                raise AttributeError("proxy for '%s' object has no "
                    "attribute '%s'" % (self._actor_class.__name__, name))
        if self._actor_attributes[name]:
            return CallableProxy(self._actor_inbox, name)
        else:
            return self._get_field(name)

    def _get_field(self, name):
        """Get a field from the actor."""
        result = gevent.event.AsyncResult()
        message = {
            'command': 'read',
            'attribute': name,
            'reply_to': result,
        }
        self._actor_inbox.put(message)
        return Future(result)

    def __setattr__(self, name, value):
        """Set a field on the actor."""
        if name.startswith('_'):
            return super(ActorProxy, self).__setattr__(name, value)
        result = gevent.event.AsyncResult()
        message = {
            'command': 'write',
            'attribute': name,
            'value': value,
            'reply_to': result,
        }
        self._actor_inbox.put(message)
        return Future(result)

    def __dir__(self):
        result = ['__class__']
        result += self.__class__.__dict__.keys()
        result += self.__dict__.keys()
        result += self._actor_attributes.keys()
        return sorted(result)


class CallableProxy(object):
    """Helper class for proxying callables."""
    def __init__(self, actor_inbox, attribute):
        self._actor_inbox = actor_inbox
        self._attribute = attribute

    def __call__(self, *args, **kwargs):
        result = gevent.event.AsyncResult()
        message = {
            'command': 'call',
            'attribute': self._attribute,
            'args': args,
            'kwargs': kwargs,
            'reply_to': result,
        }
        self._actor_inbox.put(message)
        return Future(result)
