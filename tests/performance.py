import time

from pykka import ActorRegistry, ThreadingActor


def time_it(func):
    start = time.time()
    func()
    print('{!r} took {:.3f}s'.format(func.__name__, time.time() - start))


class SomeObject(object):
    pykka_traversable = False
    cat = 'bar.cat'

    def func(self):
        pass


class AnActor(ThreadingActor):
    bar = SomeObject()
    bar.pykka_traversable = True

    foo = 'foo'

    def __init__(self):
        super(AnActor, self).__init__()
        self.cat = 'quox'

    def func(self):
        pass


def test_direct_plain_attribute_access():
    actor = AnActor.start().proxy()
    for _ in range(10000):
        actor.foo.get()


def test_direct_callable_attribute_access():
    actor = AnActor.start().proxy()
    for _ in range(10000):
        actor.func().get()


def test_traversable_plain_attribute_access():
    actor = AnActor.start().proxy()
    for _ in range(10000):
        actor.bar.cat.get()


def test_traversable_callable_attribute_access():
    actor = AnActor.start().proxy()
    for _ in range(10000):
        actor.bar.func().get()


if __name__ == '__main__':
    try:
        time_it(test_direct_plain_attribute_access)
        time_it(test_direct_callable_attribute_access)
        time_it(test_traversable_plain_attribute_access)
        time_it(test_traversable_callable_attribute_access)
    finally:
        ActorRegistry.stop_all()
