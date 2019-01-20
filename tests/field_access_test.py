import unittest

import pytest

from pykka import ThreadingActor


class SomeObject(object):
    pykka_traversable = False
    baz = 'bar.baz'

    _private_field = 'secret'


class ActorWithFields(object):
    foo = 'foo'

    bar = SomeObject()
    bar.pykka_traversable = True

    _private_field = 'secret'


class FieldAccessTest(object):
    def setUp(self):
        self.proxy = self.ActorWithFields.start().proxy()

    def tearDown(self):
        self.proxy.stop()

    def test_actor_field_can_be_read_using_get_postfix(self):
        assert self.proxy.foo.get() == 'foo'

    def test_actor_field_can_be_set_using_assignment(self):
        assert self.proxy.foo.get() == 'foo'

        self.proxy.foo = 'foo2'

        assert self.proxy.foo.get() == 'foo2'

    def test_private_field_access_raises_exception(self):
        with pytest.raises(AttributeError):
            self.proxy._private_field.get()

    def test_attr_of_traversable_attr_can_be_read(self):
        assert self.proxy.bar.baz.get() == 'bar.baz'


def ConcreteFieldAccessTest(actor_class):
    class C(FieldAccessTest, unittest.TestCase):
        class ActorWithFields(ActorWithFields, actor_class):
            pass

    C.__name__ = '%sFieldAccessTest' % actor_class.__name__
    return C


ThreadingFieldAccessTest = ConcreteFieldAccessTest(ThreadingActor)


try:
    from pykka.gevent import GeventActor
except ImportError:
    pass
else:
    GeventFieldAccessTest = ConcreteFieldAccessTest(GeventActor)


try:
    from pykka.eventlet import EventletActor
except ImportError:
    pass
else:
    EventletFieldAccessTest = ConcreteFieldAccessTest(EventletActor)
