from multiprocessing import Queue
from multiprocessing.dummy import Process
import sys

from pykka.proxy import ActorProxy
from pykka.registry import ActorRegistry
from pykka.utils import unpickle_connection


class Actor(Process):
    """
    A concurrently running actor.

    To create an actor:

    1. subclass :class:`Actor`,
    2. implement your methods, including `__init__()`, as usual,
    3. call :meth:`Actor.start()` on the actor class, passing the method any
       arguments for your constructor.

    To stop an actor, call :meth:`Actor.stop()`.
    """

    @classmethod
    def start(cls, *args, **kwargs):
        """
        Start the actor in its own thread and register it in the
        :class:`ActorRegistry`.

        Pass any arguments for the class constructor to this method instead.

        Returns a :class:`ActorProxy` which can be used to access the actor in
        a safe manner.
        """
        self = cls(*args, **kwargs)
        super(cls, self).__init__()
        self.inbox = Queue()
        self._proxy = ActorProxy(self)

        ActorRegistry.register(self._proxy)

        self.daemon = True
        super(Actor, self).start()

        return self._proxy

    def stop(self):
        """
        Stop the actor and terminate its thread.

        The actor will not stop until it is done processing the current
        message.
        """
        self.runnable = False
        ActorRegistry.unregister(self._proxy)

    def run(self):
        self.runnable = True
        try:
            while self.runnable:
                self._event_loop()
        except KeyboardInterrupt:
            sys.exit()

    def _event_loop(self):
        """The actor's event loop which is called continously to handle
        incoming messages, one at the time."""
        message = self.inbox.get()
        response = self._react(message)
        if 'reply_to' in message:
            connection = unpickle_connection(message['reply_to'])
            try:
                connection.send(response)
            except IOError:
                pass

    def _react(self, message):
        """Reacts to messages sent to the actor."""
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

    def get_attributes(self):
        """Returns a dict where the keys are all the available attributes and
        the value is whether the attribute is callable."""
        result = {}
        for attr in dir(self):
            if not attr.startswith('_'):
                result[attr] = callable(getattr(self, attr))
        return result
