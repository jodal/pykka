from multiprocessing import Queue, Pipe
from multiprocessing.dummy import Process
from multiprocessing.reduction import reduce_connection
import pickle
import sys

def pickle_connection(connection):
    return pickle.dumps(reduce_connection(connection))

def unpickle_connection(pickled_connection):
    # From http://stackoverflow.com/questions/1446004
    (func, args) = pickle.loads(pickled_connection)
    return func(*args)


class Actor(Process):
    def __init__(self, **kwargs):
        super(Actor, self).__init__()
        self.__dict__.update(kwargs)
        self.runnable = True
        self.inbox = Queue()

    def run(self):
        try:
            self.run_inside_try()
        except KeyboardInterrupt:
            sys.exit()

    def run_inside_try(self):
        while self.runnable:
            message = self.inbox.get()
            response = self.react(message)
            if 'reply_to' in message:
                connection = unpickle_connection(message['reply_to'])
                try:
                    connection.send(response)
                except IOError:
                    pass

    def react(self, message):
        if message['command'] == 'call':
            return getattr(self, message['attribute'])(
                *message['args'], **message['kwargs'])
        if message['command'] == 'read':
            return getattr(self, message['attribute'])
        if message['command'] == 'write':
            return setattr(self, message['attribute'], message['value'])
        raise NotImplementedError

    def start(self):
        super(Actor, self).start()
        return ActorProxy(self)

    def stop(self):
        self.runnable = False

    def get_attributes(self):
        """Returns a dict where the keys are all the available attributes and
        the value is whether the attribute is callable."""
        result = {}
        for attr in dir(self):
            if not attr.startswith('_'):
                result[attr] = callable(getattr(self, attr))
        return result


class ActorProxy(object):
    def __init__(self, actor):
        self._actor_name = actor.__class__.__name__
        self._actor_inbox = actor.inbox
        self._actor_attributes = actor.get_attributes()

    def __getattr__(self, name):
        if not name in self._actor_attributes:
            self._actor_attributes = self.get_attributes().get()
            if not name in self._actor_attributes:
                raise AttributeError("proxy for '%s' object has no "
                    "attribute '%s'" % (self._actor_name, name))
        if self._actor_attributes[name]:
            return CallableProxy(self._actor_inbox, name)
        else:
            return self._get_field(name)

    def _get_field(self, name):
        (read_end, write_end) = Pipe(duplex=False)
        message = {
            'command': 'read',
            'attribute': name,
            'reply_to': pickle_connection(write_end),
        }
        self._actor_inbox.put(message)
        return Future(read_end)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            return super(ActorProxy, self).__setattr__(name, value)
        (read_end, write_end) = Pipe(duplex=False)
        message = {
            'command': 'write',
            'attribute': name,
            'value': value,
            'reply_to': pickle_connection(write_end),
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
            'reply_to': pickle_connection(write_end),
        }
        self._actor_inbox.put(message)
        return Future(read_end)


class Future(object):
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
