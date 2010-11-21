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


class ActorProxy(object):
    def __init__(self, actor):
        self._actor_inbox = actor.inbox
        self._can_call = dict([(attr, callable(getattr(actor, attr)))
            for attr in dir(actor) if not attr.startswith('_')])

    def __getattr__(self, name):
        if self._can_call[name]:
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

    def get(self):
        self.connection.poll(None)
        return self.connection.recv()
