"""
Pykka is a concurrency abstraction which makes actors look like regular
objects.

See http://jodal.github.com/pykka/ for more information.
"""

from multiprocessing import Queue, Pipe
from multiprocessing.dummy import Process
from multiprocessing.reduction import reduce_connection
import pickle
import sys
import threading


__all__ = ['Actor', 'ActorRegistry', 'get_all', 'wait_all']


VERSION = (0, 4)

def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if len(VERSION) > 2:
        version = '%s.%s' % (version, VERSION[2])
    return version


class ActorRegistry(object):
    """
    Registry which provides easy access to all running actors.

    Contains global state, but should be thread-safe.
    """

    _actors = []
    _actors_lock = threading.RLock()

    @classmethod
    def get_all(cls):
        """Get all running actors"""
        with cls._actors_lock:
            return cls._actors[:]

    @classmethod
    def get_by_class(cls, actor_class):
        """Get all running actors of the given class"""
        with cls._actors_lock:
            return filter(lambda a: a._actor_class == actor_class, cls._actors)

    @classmethod
    def get_by_class_name(cls, actor_class_name):
        """Get all running actors of the given class name"""
        with cls._actors_lock:
            return filter(
                lambda a: a._actor_class.__name__ == actor_class_name,
                cls._actors)

    @classmethod
    def register(cls, actor):
        """
        Register an actor in the registry.

        This is done automatically when an actor is started.
        """
        with cls._actors_lock:
            cls._actors.append(actor)

    @classmethod
    def stop_all(cls):
        """
        Stops all running actors.

        Returns a list of futures for all the stopping actors, so that you can
        block until they have stopped if you need to.
        """
        with cls._actors_lock:
            return [a.stop() for a in cls._actors]

    @classmethod
    def unregister(cls, actor):
        """
        Remove an actor from the registry.

        This is done automatically when an actor is stopped.
        """
        with cls._actors_lock:
            cls._actors.remove(actor)


class Actor(Process):
    """
    A concurrently running actor.

    To create an actor:

    1. subclass :class:`Actor`,
    2. implement your methods as usual,
    3. instantiate the actor as usual,
    4. call :meth:`Actor.start()` on the actor instance.

    To stop an actor, call :meth:`Actor.stop()`.
    """

    def __init__(self, **kwargs):
        super(Actor, self).__init__()
        self.__dict__.update(kwargs)
        self.runnable = True
        self.inbox = Queue()
        self._proxy = None

    def start(self):
        super(Actor, self).start()
        self._proxy = ActorProxy(self)
        ActorRegistry.register(self._proxy)
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
            connection = _unpickle_connection(message['reply_to'])
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
        (read_end, write_end) = Pipe(duplex=False)
        message = {
            'command': 'read',
            'attribute': name,
            'reply_to': _pickle_connection(write_end),
        }
        self._actor_inbox.put(message)
        return Future(read_end)

    def __setattr__(self, name, value):
        """Set a field on the actor."""
        if name.startswith('_'):
            return super(ActorProxy, self).__setattr__(name, value)
        (read_end, write_end) = Pipe(duplex=False)
        message = {
            'command': 'write',
            'attribute': name,
            'value': value,
            'reply_to': _pickle_connection(write_end),
        }
        self._actor_inbox.put(message)
        return Future(read_end)

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
        (read_end, write_end) = Pipe(duplex=False)
        message = {
            'command': 'call',
            'attribute': self._attribute,
            'args': args,
            'kwargs': kwargs,
            'reply_to': _pickle_connection(write_end),
        }
        self._actor_inbox.put(message)
        return Future(read_end)


class Future(object):
    """
    A :class:`Future` is a handle to a value which will be available in the
    future.

    Typically returned by calls to actor methods or accesses to actor fields.

    To get hold of the encapsulated value, call :meth:`Future.get()`.
    """
    def __init__(self, connection):
        self.connection = connection

    def __str__(self):
        return str(self.get())

    def get(self, timeout=None):
        """
        Get the value encapsulated by the future.

        Will block until the value is available, unless the optional *timeout*
        argument is set to:

        - :class:`None` -- block forever (default)
        - :class:`False` -- return immediately
        - numeric -- timeout after given number of seconds
        """
        if timeout is False:
            poll_args = []
        else:
            poll_args = [timeout]
        if self.connection.poll(*poll_args):
            return self.connection.recv()
        else:
            return None

    def wait(self, timeout=None):
        """
        Block until the future is available.

        An alias for :meth:`get`, but with a name that is more describing if
        you do not care about the return value.
        """
        return self.get(timeout)


def get_all(futures, timeout=None):
    """
    Get all the values encapsulated by the given features.

    :attr:`timeout` has the same behaviour as for :meth:`Future.get`.
    """
    return map(lambda future: future.wait(timeout), futures)


def wait_all(futures, timeout=None):
    """
    Block until all the given features are available.

    An alias for :func:`get_all`, but with a name that is more describing if
    you do not care about the return values.
    """
    return get_all(futures, timeout)


def _pickle_connection(connection):
    """Pickles a connection object"""
    return pickle.dumps(reduce_connection(connection))


def _unpickle_connection(pickled_connection):
    """Unpickles a connection object"""
    # From http://stackoverflow.com/questions/1446004
    (func, args) = pickle.loads(pickled_connection)
    return func(*args)
