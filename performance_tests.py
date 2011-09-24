import time

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

def time_it(func):
    start = time.time()
    func()
    print '%s took %.3fs' % (func.func_name, time.time() - start)


class SomeObject(object):
    baz = 'bar.baz'

class AnActor(ThreadingActor):
    bar = SomeObject()
    bar.pykka_traversable = True

    foo = 'foo'

    def __init__(self):
        self.baz = 'quox'

    def func(self):
        pass

def test_direct_attribute_access():
    actor = AnActor.start().proxy()
    for i in range(10000):
        foo = actor.foo

def test_traversible_attribute_access():
    actor = AnActor.start().proxy()
    for i in range(10000):
        foo = actor.bar.baz

if __name__ == '__main__':
    try:
        time_it(test_direct_attribute_access)
        time_it(test_traversible_attribute_access)
    finally:
        ActorRegistry.stop_all()
